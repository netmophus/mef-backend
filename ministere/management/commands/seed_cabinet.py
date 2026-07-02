"""Seed du cabinet du ministre (données de démonstration).

⚠️ Noms fictifs — à remplacer par les vrais membres + photos via l'admin.
Idempotent.

    python manage.py seed_cabinet
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from ministere.models import MembreCabinet

# (nom, fonction)
MEMBRES = [
    ('M. Abdoulaye Issoufou', 'Directeur de Cabinet'),
    ('Mme Hadiza Saïdou', 'Directrice Adjointe de Cabinet'),
    ('M. Ibrahim Maïga', 'Chef de Cabinet'),
    ('Mme Fatouma Oumarou', 'Secrétaire Particulière du Ministre'),
    ('M. Salifou Garba', 'Conseiller Technique — Finances Publiques'),
    ('M. Moussa Adamou', 'Conseiller Technique — Fiscalité et Douanes'),
    ('Mme Rakiatou Hassane', 'Conseillère en Communication'),
    ('M. Ali Mahamadou', 'Conseiller Juridique'),
]


class Command(BaseCommand):
    help = 'Pré-remplit le cabinet du ministre (données de démonstration).'

    @transaction.atomic
    def handle(self, *args, **options):
        MembreCabinet.objects.all().delete()
        for i, (nom, fonction) in enumerate(MEMBRES):
            MembreCabinet.objects.create(nom=nom, fonction=fonction, ordre=i)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(MEMBRES)} membres du cabinet crees.'))
