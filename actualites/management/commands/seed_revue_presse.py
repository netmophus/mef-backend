"""Seed de la revue de presse (Actualités › Revue de presse).

Reproduit les numéros par année de l'ancien site. Liens PDF en « # » — à
brancher via l'admin. Idempotent.

    python manage.py seed_revue_presse
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from actualites.models import NumeroRevue

# Nombre de numéros par année (repris du frontend).
COMPTES = {
    2025: 15, 2024: 47, 2023: 48, 2022: 47, 2021: 48,
    2020: 47, 2019: 52, 2018: 53, 2017: 52, 2016: 43,
}


def titres(annee, n):
    """Titres d'une année, du plus récent numéro au plus ancien."""
    if annee == 2025:
        # Le n°15 ne porte pas la mention « Economie ».
        return ['Revue de Presse n°15 - 2025'] + [
            f'Revue de Presse Economie n°{str(14 - i).zfill(2)} - 2025' for i in range(14)
        ]
    return [f'Revue de Presse Economie n°{str(n - i).zfill(2)} - {annee}' for i in range(n)]


class Command(BaseCommand):
    help = "Pré-remplit la revue de presse (numéros par année, démo)."

    @transaction.atomic
    def handle(self, *args, **options):
        NumeroRevue.objects.all().delete()
        objets = []
        for annee, n in COMPTES.items():
            for i, titre in enumerate(titres(annee, n)):
                objets.append(NumeroRevue(annee=annee, titre=titre, lien='#', ordre=i))
        NumeroRevue.objects.bulk_create(objets)
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(objets)} numeros de revue de presse crees.'))
