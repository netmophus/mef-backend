"""Seed des « Accès rapides » de l'accueil, identiques au frontend (QuickAccess.js).

Idempotent : reconstruit la liste à chaque exécution.

    python manage.py seed_quicklinks
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from accueil.models import QuickLink

# Accès rapides — services & démembrements (URLs officielles vérifiées).
# (nom, icône, couleur début, couleur fin, href)
LIENS = [
    ('e-SECeF', 'computer', '#0a5ca8', '#002B55', '#'),
    ('Marchés publics', 'gavel', '#37a06a', '#1F6E42', 'https://www.marchespublics.ne/'),
    ('Impôts (DGI)', 'receipt_long', '#caa029', '#8a6a14', 'https://www.impots.gouv.ne/'),
    ('Douanes (DGD)', 'public', '#ef9038', '#B85E18', 'http://www.douanes.gouv.ne/'),
    ('Trésor (DGTCP)', 'account_balance', '#0a5ca8', '#002B55', 'https://tresor.ne/'),
    ('SYGMEF', 'description', '#2f8f7a', '#1f6e5e', '#'),
    ('Cour des comptes', 'gavel', '#4b6cb7', '#2a3f7a', 'https://www.courdescomptes.ne/'),
    ('MDE', 'payments', '#b98a2e', '#7a5a14', 'https://mde.ne/'),
    ('Finance inclusive (SNFI)', 'payments', '#37a06a', '#1F6E42', 'http://www.se-snfi.ne/'),
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
