import hashlib
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import CompteurRegistre, EvenementCourrier

TAILLE_MAX_SCAN = 25 * 1024 * 1024  # 25 Mo


def generer_numero(registre):
    """Numéro d'ordre fiable via compteur verrouillé (select_for_update).

    Format : {CODE}-{ANNEE}-{00000}. JAMAIS de MAX()+1.
    """
    annee = date.today().year
    with transaction.atomic():
        compteur, _ = (
            CompteurRegistre.objects
            .select_for_update()
            .get_or_create(registre=registre, annee=annee)
        )
        compteur.dernier_numero += 1
        compteur.save(update_fields=['dernier_numero'])
        return f'{registre.code}-{annee}-{compteur.dernier_numero:05d}'


def valider_scan(fichier):
    """Valide un scan PDF : extension .pdf + signature %PDF + taille ≤ 25 Mo.

    Lève django ValidationError (message en français) en cas de problème.
    """
    nom = (fichier.name or '').lower()
    if not nom.endswith('.pdf'):
        raise ValidationError('Le fichier doit être un PDF (extension .pdf).')
    if fichier.size > TAILLE_MAX_SCAN:
        raise ValidationError('Le fichier dépasse la taille maximale autorisée (25 Mo).')
    debut = fichier.read(5)
    fichier.seek(0)
    if not debut.startswith(b'%PDF-'):
        raise ValidationError("Le fichier n'est pas un PDF valide (signature %PDF absente).")


def calculer_sha256(fichier):
    """Empreinte SHA-256 du contenu du fichier (repositionne le curseur ensuite)."""
    h = hashlib.sha256()
    for bloc in fichier.chunks():
        h.update(bloc)
    fichier.seek(0)
    return h.hexdigest()


def journaliser(courrier, type_evenement, acteur, details=None):
    """Crée un EvenementCourrier (toute transition passe par ici)."""
    return EvenementCourrier.objects.create(
        courrier=courrier, type=type_evenement, acteur=acteur, details=details or {},
    )


# === Imputations (lot C2) ====================================================
from django.core.exceptions import ValidationError  # noqa: E402
from django.utils import timezone  # noqa: E402
from .models import Imputation  # noqa: E402


class ConflitImputation(Exception):
    """Erreur de conflit d'état (→ HTTP 409)."""


def _imputations_actives(courrier):
    return courrier.imputations.filter(annulee_le__isnull=True)


def creer_imputation(courrier, *, direction_cible, instruction, delai, commentaire,
                     impute_par, imputation_mere=None):
    if courrier.statut == 'CLASSE':
        raise ValidationError('Impossible d’imputer un courrier classé.')

    est_sous = imputation_mere is not None
    if est_sous:
        if not imputation_mere.active:
            raise ValidationError('L’imputation mère a été annulée.')
        if imputation_mere.accuse_le is None:
            raise ValidationError('Impossible de sous-imputer une imputation non accusée.')
        if direction_cible.id not in imputation_mere.direction_cible.descendant_ids():
            raise ValidationError('La direction cible doit appartenir au sous-arbre de l’imputation mère.')

    if instruction == 'POUR_TRAITEMENT':
        deja = _imputations_actives(courrier).filter(
            imputation_mere=imputation_mere, instruction='POUR_TRAITEMENT')
        if deja.exists():
            raise ValidationError('Il existe déjà une imputation « pour traitement » active à ce niveau.')

    imp = Imputation.objects.create(
        courrier=courrier, imputation_mere=imputation_mere, direction_cible=direction_cible,
        instruction=instruction, delai=delai, commentaire=commentaire or '', impute_par=impute_par)
    journaliser(courrier, 'SOUS_IMPUTATION' if est_sous else 'IMPUTATION', impute_par,
                {'direction': direction_cible.sigle, 'instruction': instruction})
    if courrier.statut == 'ENREGISTRE':
        courrier.statut = 'IMPUTE'
        courrier.save(update_fields=['statut', 'modifie_le'])
    return imp


def accuser_imputation(imp, user):
    if not imp.active:
        raise ValidationError('Imputation annulée.')
    if imp.accuse_le is not None:
        raise ConflitImputation('Cette imputation a déjà été accusée.')
    imp.accuse_le = timezone.now()
    imp.accuse_par = user
    imp.statut = 'ACCUSEE'
    imp.save(update_fields=['accuse_le', 'accuse_par', 'statut'])
    journaliser(imp.courrier, 'ACCUSE_RECEPTION', user, {'direction': imp.direction_cible.sigle})
    if imp.courrier.statut == 'IMPUTE':
        imp.courrier.statut = 'EN_TRAITEMENT'
        imp.courrier.save(update_fields=['statut', 'modifie_le'])
    return imp


def traiter_imputation(imp, user, commentaire):
    if not commentaire or not commentaire.strip():
        raise ValidationError('Le commentaire de traitement est obligatoire.')
    if imp.accuse_le is None:
        raise ValidationError('Impossible de traiter une imputation non accusée.')
    if imp.statut == 'TRAITEE':
        raise ConflitImputation('Imputation déjà traitée.')
    imp.statut = 'TRAITEE'
    imp.traite_le = timezone.now()
    imp.traite_par = user
    imp.commentaire_traitement = commentaire.strip()
    imp.save(update_fields=['statut', 'traite_le', 'traite_par', 'commentaire_traitement'])
    journaliser(imp.courrier, 'MARQUE_TRAITE', user, {'commentaire': commentaire.strip()})
    if imp.est_premier_niveau and imp.instruction == 'POUR_TRAITEMENT':
        imp.courrier.statut = 'TRAITE'
        imp.courrier.save(update_fields=['statut', 'modifie_le'])
    return imp


def annuler_imputation(imp, user):
    if not imp.active:
        raise ConflitImputation('Imputation déjà annulée.')
    if imp.accuse_le is not None:
        raise ConflitImputation('Impossible d’annuler une imputation déjà accusée.')
    if imp.sous_imputations.filter(annulee_le__isnull=True).exists():
        raise ValidationError('Impossible d’annuler : des sous-imputations existent.')
    imp.annulee_le = timezone.now()
    imp.annulee_par = user
    imp.save(update_fields=['annulee_le', 'annulee_par'])
    journaliser(imp.courrier, 'RETOUR_IMPUTATION', user, {'direction': imp.direction_cible.sigle})
    if not _imputations_actives(imp.courrier).exists() and imp.courrier.statut == 'IMPUTE':
        imp.courrier.statut = 'ENREGISTRE'
        imp.courrier.save(update_fields=['statut', 'modifie_le'])
    return imp
