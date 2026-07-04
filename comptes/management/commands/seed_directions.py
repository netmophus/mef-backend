"""Seed des directions de premier niveau du Ministère.

⚠️ Rattachements provisoires (les DG sous le SG) — à affiner ultérieurement.
Idempotent (get_or_create par sigle).

    python manage.py seed_directions
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from comptes.models import Direction

# Structures de tête (sans parent)
TETE = [
    ('CAB', 'Cabinet du Ministre'),
    ('SG', 'Secrétariat Général'),
]

# Directions rattachées au Secrétariat Général (provisoire)
SOUS_SG = [
    ('DGB', 'Direction Générale du Budget'),
    ('DGI', 'Direction Générale des Impôts'),
    ('DGD', 'Direction Générale des Douanes'),
    ('DGTCP', 'Direction Générale du Trésor et de la Comptabilité Publique'),
    ('DGEP', "Direction Générale de l'Économie et de la Planification"),
    ('DRH', 'Direction des Ressources Humaines'),
    ('DSI', "Direction des Systèmes d'Information"),
]


class Command(BaseCommand):
    help = 'Pré-remplit les directions de premier niveau du Ministère.'

    @transaction.atomic
    def handle(self, *args, **options):
        ordre = 0
        for sigle, nom in TETE:
            Direction.objects.update_or_create(
                sigle=sigle, defaults={'nom': nom, 'parent': None, 'ordre': ordre})
            ordre += 1

        sg = Direction.objects.get(sigle='SG')
        for sigle, nom in SOUS_SG:
            Direction.objects.update_or_create(
                sigle=sigle, defaults={'nom': nom, 'parent': sg, 'ordre': ordre})
            ordre += 1

        total = Direction.objects.count()
        self.stdout.write(self.style.SUCCESS(f'[OK] {total} directions creees/mises a jour.'))
