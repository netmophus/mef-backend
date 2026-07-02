"""Seed des documents budgétaires (démo) — rubrique « lois-de-finances ».

⚠️ Documents fictifs (lien « # ») — à remplacer par les vrais PDF via l'admin.
Idempotent : ne touche qu'à la rubrique « lois-de-finances ».

    python manage.py seed_budget
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from budget.models import DocumentBudget

RUBRIQUE = 'lois-de-finances'

# Année : liste de (type, titre). LFI = initiale, LFR = rectificative.
DOCS = {
    2027: [('Loi de finances initiale', 'Loi de finances pour 2027')],
    2026: [('Loi de finances initiale', 'Loi de finances pour 2026'),
           ('Rectificative', 'Loi de finances rectificative 2026')],
    2025: [('Loi de finances initiale', 'Loi de finances pour 2025'),
           ('Rectificative', 'Loi de finances rectificative 2025')],
    2024: [('Loi de finances initiale', 'Loi de finances pour 2024')],
    2023: [('Loi de finances initiale', 'Loi de finances pour 2023'),
           ('Rectificative', 'Loi de finances rectificative 2023')],
    2022: [('Loi de finances initiale', 'Loi de finances pour 2022')],
    2021: [('Loi de finances initiale', 'Loi de finances pour 2021')],
    2020: [('Loi de finances initiale', 'Loi de finances pour 2020'),
           ('Rectificative', 'Loi de finances rectificative 2020')],
}


class Command(BaseCommand):
    help = "Pré-remplit les documents budgétaires (rubrique lois-de-finances, démo)."

    @transaction.atomic
    def handle(self, *args, **options):
        DocumentBudget.objects.filter(rubrique=RUBRIQUE).delete()
        total = 0
        for annee, items in DOCS.items():
            for i, (type_, titre) in enumerate(items):
                DocumentBudget.objects.create(
                    rubrique=RUBRIQUE, annee=annee, titre=titre, type=type_,
                    lien='#', ordre=i,
                )
                total += 1
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {total} documents budgetaires crees (rubrique {RUBRIQUE}).'))
