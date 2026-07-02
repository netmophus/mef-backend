"""Seed des lois de règlement (rubrique « lois-de-reglement »).

⚠️ Documents fictifs (lien « # ») — à remplacer par les vrais PDF via l'admin.
Idempotent : ne touche qu'à la rubrique « lois-de-reglement ».

    python manage.py seed_lois_reglement
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from budget.models import DocumentBudget

RUBRIQUE = 'lois-de-reglement'

# Une loi de règlement par gestion (année budgétaire), de 1997 à 2021.
# (2001 et les années récentes non encore adoptées sont omises.)
ANNEES = [a for a in range(1997, 2022) if a != 2001]


class Command(BaseCommand):
    help = "Pré-remplit les lois de règlement (rubrique lois-de-reglement, démo)."

    @transaction.atomic
    def handle(self, *args, **options):
        DocumentBudget.objects.filter(rubrique=RUBRIQUE).delete()
        for annee in ANNEES:
            DocumentBudget.objects.create(
                rubrique=RUBRIQUE, annee=annee,
                titre=f'Loi de règlement de la gestion {annee}',
                type='Loi de règlement', lien='#', ordre=0,
            )
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(ANNEES)} lois de reglement creees (rubrique {RUBRIQUE}).'))
