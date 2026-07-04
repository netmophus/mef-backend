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
from datetime import timedelta  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.utils import timezone  # noqa: E402
from .models import Imputation  # noqa: E402

DELAI_ANTI_RELANCE = timedelta(hours=24)  # anti-harcèlement


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


def sous_imputations_ouvertes(imp):
    """Sous-imputations actives non traitées, récursif (pour l'avertissement 0.2)."""
    res = []
    for s in imp.sous_imputations.filter(annulee_le__isnull=True).exclude(statut='TRAITEE'):
        res.append(s)
        res.extend(sous_imputations_ouvertes(s))
    return res


def traiter_imputation(imp, user, commentaire, clore_sous=False):
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
    # 0.2 : clôture des sous-imputations ouvertes par le niveau supérieur.
    if clore_sous:
        for s in sous_imputations_ouvertes(imp):
            s.statut = 'TRAITEE'
            s.traite_le = timezone.now()
            s.traite_par = user
            s.commentaire_traitement = 'Clôturé par le niveau supérieur.'
            s.save(update_fields=['statut', 'traite_le', 'traite_par', 'commentaire_traitement'])
            journaliser(s.courrier, 'CLOTURE_PAR_NIVEAU_SUPERIEUR', user,
                        {'direction': s.direction_cible.sigle})
    if imp.est_premier_niveau and imp.instruction == 'POUR_TRAITEMENT':
        imp.courrier.statut = 'TRAITE'
        imp.courrier.save(update_fields=['statut', 'modifie_le'])
    return imp


def relancer_imputation(imp, user, commentaire=''):
    """Relance MANUELLE (lot C3) : trace un événement + met en évidence dans la
    bannette du destinataire. Pas d'email. 409 si traitée/annulée ou < 24 h."""
    if not imp.active:
        raise ConflitImputation('Imputation annulée.')
    if imp.statut == 'TRAITEE':
        raise ConflitImputation('Impossible de relancer une imputation déjà traitée.')
    maintenant = timezone.now()
    if imp.derniere_relance_le and (maintenant - imp.derniere_relance_le) < DELAI_ANTI_RELANCE:
        raise ConflitImputation('Une relance a déjà été envoyée il y a moins de 24 heures.')
    imp.derniere_relance_le = maintenant
    imp.save(update_fields=['derniere_relance_le'])
    journaliser(imp.courrier, 'RELANCE', user,
                {'direction': imp.direction_cible.sigle, 'commentaire': (commentaire or '').strip()})
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


# === Courrier DÉPART (lot C4) ================================================
from .models import Registre, Courrier, DestinataireCopie  # noqa: E402

SIGLE_MINISTERE = 'MEF'


def generer_reference_depart(structure_emettrice):
    """Réserve un numéro au registre DEP et construit la référence officielle.

    reference = NNNN/MEF/{chaîne sigles ancêtres→structure}/{année}
    numero_ordre interne = DEP-{année}-{NNNNN} (cohérence C1)."""
    registre = Registre.objects.get(code='DEP')
    annee = date.today().year
    with transaction.atomic():
        compteur, _ = (CompteurRegistre.objects.select_for_update()
                       .get_or_create(registre=registre, annee=annee))
        compteur.dernier_numero += 1
        compteur.save(update_fields=['dernier_numero'])
        n = compteur.dernier_numero
    chaine = '/'.join(d.sigle for d in structure_emettrice.get_ancestors(inclure_soi=True)
                      if d.sigle != SIGLE_MINISTERE)  # exclut la racine ministère si présente
    numero_ordre = f'{registre.code}-{annee}-{n:05d}'
    reference = f'{n:04d}/{SIGLE_MINISTERE}/{chaine}/{annee}'
    return registre, numero_ordre, reference


def lier_et_cloturer(depart, origine, acteur):
    """Liaison réponse→arrivée. Le PREMIER lien clôt l'arrivée (imputations + statut)."""
    journaliser(origine, 'REPONSE_LIEE', acteur,
                {'reference': depart.reference_complete, 'depart_id': depart.id})
    if origine.statut == 'TRAITE':
        return  # déjà traité : liaison seule, pas de re-clôture
    for imp in origine.imputations.filter(annulee_le__isnull=True).exclude(statut='TRAITEE'):
        imp.statut = 'TRAITEE'
        imp.traite_le = timezone.now()
        imp.traite_par = acteur
        imp.commentaire_traitement = f'Clôturé par la réponse {depart.reference_complete}.'
        imp.save(update_fields=['statut', 'traite_le', 'traite_par', 'commentaire_traitement'])
        journaliser(origine, 'CLOTURE_PAR_REPONSE', acteur,
                    {'direction': imp.direction_cible.sigle, 'reference': depart.reference_complete})
    origine.statut = 'TRAITE'
    origine.save(update_fields=['statut', 'modifie_le'])


def creer_depart(*, enregistre_par, structure_emettrice, objet, correspondant, signataire_nom='',
                 signataire_qualite='', date_signature=None, ampliations=None, courrier_origine=None,
                 scan=None, nombre_pieces=1, confidentialite='ORDINAIRE'):
    """Enregistre un courrier départ signé. Scan optionnel à la création (obligatoire
    à l'expédition). Si courrier_origine : liaison + clôture automatique de l'arrivée."""
    if courrier_origine is not None:
        if courrier_origine.sens != 'ARRIVEE':
            raise ValidationError("Le courrier d'origine doit être un courrier arrivée.")
        if courrier_origine.statut == 'CLASSE':
            raise ValidationError("Impossible de lier une réponse à un courrier classé sans suite.")

    registre, numero_ordre, reference = generer_reference_depart(structure_emettrice)
    courrier = Courrier(
        registre=registre, numero_ordre=numero_ordre, sens='DEPART', enregistre_par=enregistre_par,
        structure_emettrice=structure_emettrice, objet=objet, correspondant=correspondant,
        signataire_nom=signataire_nom or '', signataire_qualite=signataire_qualite or '',
        date_signature=date_signature, reference_complete=reference,
        date_document=date_signature or date.today(), date_arrivee=date.today(),
        nombre_pieces=nombre_pieces or 1, confidentialite=confidentialite or 'ORDINAIRE',
        courrier_origine=courrier_origine, statut='ENREGISTRE')
    if scan is not None:
        courrier.hash_sha256 = calculer_sha256(scan)
        courrier.scan = scan
    courrier.save()
    journaliser(courrier, 'ENREGISTREMENT', enregistre_par,
                {'reference': reference, 'sens': 'DEPART'})
    for c in (ampliations or []):
        DestinataireCopie.objects.get_or_create(courrier=courrier, correspondant=c,
                                                defaults={'type': 'AMPLIATION'})
    if courrier_origine is not None:
        lier_et_cloturer(courrier, courrier_origine, enregistre_par)
    return courrier


def expedier_courrier(depart, user, date_expedition=None):
    if depart.sens != 'DEPART':
        raise ValidationError("Seul un courrier départ peut être expédié.")
    if not depart.scan:
        raise ConflitImputation("Le scan signé est requis avant l'expédition.")
    if depart.expedie_le:
        raise ConflitImputation('Ce courrier a déjà été expédié.')
    depart.expedie_le = date_expedition or date.today()
    depart.save(update_fields=['expedie_le', 'modifie_le'])
    journaliser(depart, 'EXPEDITION', user, {'date': str(depart.expedie_le)})
    return depart


def decharger_courrier(depart, user, date_decharge, commentaire=''):
    if depart.sens != 'DEPART':
        raise ValidationError("Seul un courrier départ peut recevoir une décharge.")
    if not depart.expedie_le:
        raise ConflitImputation("Le courrier n'a pas encore été expédié.")
    if depart.decharge_recue_le:
        raise ConflitImputation('La décharge a déjà été pointée.')
    depart.decharge_recue_le = date_decharge
    depart.decharge_commentaire = commentaire or ''
    depart.statut = 'CLASSE'  # cycle départ court : enregistré → expédié → déchargé/classé
    depart.save(update_fields=['decharge_recue_le', 'decharge_commentaire', 'statut', 'modifie_le'])
    journaliser(depart, 'DECHARGE_RECUE', user, {'date': str(date_decharge), 'commentaire': commentaire or ''})
    return depart
