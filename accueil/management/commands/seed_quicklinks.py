"""Seed des « Accès rapides » de l'accueil, identiques au frontend (QuickAccess.js).

Idempotent : reconstruit la liste à chaque exécution.

    python manage.py seed_quicklinks
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from accueil.models import QuickLink

# Données reprises telles quelles de QuickAccess.js
# (nom, icône, couleur début, couleur fin, href)
LIENS = [
    ('e-SECeF', 'computer', '#0a5ca8', '#002B55', '#'),
    ('Marchés publics', 'gavel', '#37a06a', '#1F6E42', '#'),
    ('SYGMEF', 'account_balance', '#ef9038', '#B85E18', '#'),
    ('DGI', 'receipt_long', '#caa029', '#8a6a14', '#'),
]


class Command(BaseCommand):
    help = "Pré-remplit les « Accès rapides » avec les données actuelles du frontend."

    @transaction.atomic
    def handle(self, *args, **options):
        QuickLink.objects.all().delete()
        for i, (nom, icone, c1, c2, href) in enumerate(LIENS):
            QuickLink.objects.create(
                nom=nom, icone=icone, couleur_debut=c1, couleur_fin=c2, href=href, ordre=i,
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(LIENS)} acces rapides crees.'))
