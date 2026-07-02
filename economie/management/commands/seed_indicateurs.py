"""Seed des indicateurs macroéconomiques, repris du frontend (MacroIndicators.js).

⚠️ Chiffres de démonstration — à confirmer / brancher sur une source officielle.
Idempotent.

    python manage.py seed_indicateurs
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from economie.models import IndicateurMacro, IndicateurCle

# (label, valeur, decimales, suffixe, unite, icone, couleur_debut, couleur_fin)
GRANDS = [
    ('PIB Nominal', 23170, 0, '', 'Milliards FCFA', 'paid', '#0a5ca8', '#002B55'),
    ('Croissance du PIB', 5, 0, '%', 'Estimation', 'trending_up', '#37a06a', '#1F6E42'),
    ('Inflation', 1.4, 1, '%', 'Mars 2026', 'show_chart', '#caa029', '#8a6314'),
    ('Besoins de financement', 6075.2, 1, '', 'Milliards FCFA', 'request_quote', '#ef9038', '#B85E18'),
]

# (label, valeur, maximum, couleur, note)
CLES = [
    ('Taux de croissance', 8.1, 10, '#2E8B57', '2025'),
    ("Taux d'inflation", 1.1, 10, '#E0A92E', '2025'),
    ('Déficit budgétaire', 2.7, 10, '#E07B2C', 'en % du PIB · 2025'),
    ("Taux d'endettement", 52.8, 100, '#6FB3E0', 'en % du PIB · 2025'),
]


class Command(BaseCommand):
    help = 'Pré-remplit les indicateurs macroéconomiques (données de démonstration).'

    @transaction.atomic
    def handle(self, *args, **options):
        IndicateurMacro.objects.all().delete()
        IndicateurCle.objects.all().delete()
        for i, (label, val, dec, suf, unite, icone, c1, c2) in enumerate(GRANDS):
            IndicateurMacro.objects.create(
                label=label, valeur=val, decimales=dec, suffixe=suf, unite=unite,
                icone=icone, couleur_debut=c1, couleur_fin=c2, ordre=i,
            )
        for i, (label, val, mx, couleur, note) in enumerate(CLES):
            IndicateurCle.objects.create(
                label=label, valeur=val, maximum=mx, couleur=couleur, note=note, ordre=i,
            )
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(GRANDS)} grands indicateurs + {len(CLES)} indicateurs cles crees.'))
