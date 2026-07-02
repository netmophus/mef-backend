"""Seed des liens utiles et partenaires, repris du frontend (ResourcesPartners.js).

⚠️ URL en « # » — à compléter via l'admin. Logos partenaires à téléverser.
Idempotent.

    python manage.py seed_liens_partenaires
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import LienUtile, Partenaire, BlocReforme

LIENS = [
    'Présidence de la République',
    'Primature',
    'Assemblée Nationale',
    'Cour des Comptes',
    'BCEAO',
    'ARMP',
    "Inspection Générale d'État",
]

# (nom, sigle, initiales)
PARTENAIRES = [
    ('FMI', 'Fonds Monétaire Int.', 'FMI'),
    ('Banque Mondiale', 'Groupe BM', 'BM'),
    ('BAD', 'Banque Africaine de Dév.', 'BAD'),
    ('UEMOA', 'Union économique', 'UE'),
    ('Union Européenne', 'Commission UE', 'UE'),
    ('PNUD', 'Nations Unies', 'UN'),
    ('BOAD', 'Banque Ouest-Africaine', 'BO'),
    ('BCEAO', 'Banque Centrale', 'BC'),
]


class Command(BaseCommand):
    help = 'Pré-remplit les liens utiles et partenaires (données de démonstration).'

    @transaction.atomic
    def handle(self, *args, **options):
        LienUtile.objects.all().delete()
        Partenaire.objects.all().delete()
        for i, label in enumerate(LIENS):
            LienUtile.objects.create(label=label, url='#', ordre=i)
        for i, (nom, sigle, init) in enumerate(PARTENAIRES):
            Partenaire.objects.create(nom=nom, sigle=sigle, initiales=init, url='#', ordre=i)
        # Bloc « Réforme » (singleton) — créé avec ses valeurs par défaut s'il n'existe pas.
        BlocReforme.load()
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(LIENS)} liens + {len(PARTENAIRES)} partenaires + bloc reforme crees.'))
