"""Seed des discours du ministre (données de démonstration).

⚠️ Contenu fictif — à remplacer par les vrais discours + PDF via l'admin.
Idempotent.

    python manage.py seed_discours
"""

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from ministere.models import Discours

# (titre, date, extrait, lien)
DISCOURS = [
    (
        'Présentation de la Loi de Finances 2026',
        datetime.date(2026, 1, 15),
        "Le Ministre a présenté les grandes orientations budgétaires de l'État pour "
        "l'exercice 2026, axées sur l'investissement productif et la soutenabilité de la dette.",
        '#',
    ),
    (
        'Allocution à la clôture du Forum économique national',
        datetime.date(2025, 11, 20),
        "Bilan des travaux du Forum et perspectives de relance de l'économie nationale "
        "en partenariat avec le secteur privé.",
        '#',
    ),
    (
        'Discours sur les réformes des finances publiques',
        datetime.date(2025, 9, 10),
        "Point d'étape sur la modernisation de la chaîne de la dépense et la dématérialisation "
        "des procédures (e-SECeF, DGI en ligne).",
        '#',
    ),
    (
        "Communication sur l'exécution budgétaire du 1er semestre",
        datetime.date(2025, 7, 5),
        "Présentation des résultats d'exécution du budget de l'État au premier semestre 2025 "
        "et des mesures de pilotage retenues.",
        '#',
    ),
]


class Command(BaseCommand):
    help = 'Pré-remplit les discours du ministre (données de démonstration).'

    @transaction.atomic
    def handle(self, *args, **options):
        Discours.objects.all().delete()
        for titre, date, extrait, lien in DISCOURS:
            Discours.objects.create(titre=titre, date=date, extrait=extrait, lien=lien)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(DISCOURS)} discours crees.'))
