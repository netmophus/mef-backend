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
