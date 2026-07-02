"""Seed de l'album photo du Ministre, identique au frontend (albumMinistre.js).

Idempotent : reconstruit l'album à chaque exécution.
Les portraits existants côté frontend (public/) sont copiés dans les médias
du backend pour conserver le même rendu ; les photos d'activités utilisent
une URL externe (image_url).

    python manage.py seed_album
"""

from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from ministere.models import AlbumPhoto

# Dossier public du frontend (portraits du Ministre déjà présents).
FRONTEND_PUBLIC = Path(settings.BASE_DIR).parent / 'finance-frontend' / 'public'

# (titre, categorie, fichier_public | None, image_url, (annee, mois))
PHOTOS = [
    ('Portrait officiel du Ministre', 'Portraits', 'DrRafa.jpeg', '', (2026, 2)),
    ('Le Ministre dans son cabinet', 'Portraits', 'drrafa1.jpg', '', (2026, 2)),
    ('Le Ministre en séance de travail', 'Portraits', 'drrafa2.jpg', '', (2026, 3)),

    ('Le Ministre signe des accords de financement', 'Activités', None,
     'https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1200&q=80', (2026, 5)),
    ('Le Ministre au Forum économique national', 'Activités', None,
     'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80', (2026, 4)),
    ('Le Ministre à la rencontre du secteur privé', 'Activités', None,
     'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1200&q=80', (2026, 3)),

    ('Le Ministre en audience avec le FMI', 'Audiences', None,
     'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&q=80', (2026, 5)),
    ('Le Ministre reçoit les partenaires techniques et financiers', 'Audiences', None,
     'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80', (2026, 4)),
    ('Le Ministre en réunion avec les bailleurs', 'Audiences', None,
     'https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=1200&q=80', (2026, 3)),

    ('Le Ministre au Conseil des Ministres', 'Cérémonies', None,
     'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=1200&q=80', (2026, 6)),
    ("Le Ministre lors d'une cérémonie officielle", 'Cérémonies', None,
     'https://images.unsplash.com/photo-1531545514256-b1400bc00f31?auto=format&fit=crop&w=1200&q=80', (2026, 5)),
    ('Le Ministre en visite de terrain', 'Cérémonies', None,
     'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80', (2026, 2)),
]


class Command(BaseCommand):
    help = "Pré-remplit l'album photo du Ministre (données de démonstration)."

    @transaction.atomic
    def handle(self, *args, **options):
        AlbumPhoto.objects.all().delete()
        copies = 0
        for i, (titre, categorie, fichier, url, (annee, mois)) in enumerate(PHOTOS):
            photo = AlbumPhoto(
                titre=titre, categorie=categorie, image_url=url,
                date=date(annee, mois, 1), ordre=i,
            )
            if fichier:
                source = FRONTEND_PUBLIC / fichier
                if source.exists():
                    with source.open('rb') as f:
                        photo.image.save(fichier, File(f), save=False)
                    copies += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ! portrait introuvable, image_url utilisee : {source}'))
            photo.save()

        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(PHOTOS)} photos d\'album creees ({copies} portrait(s) copie(s)).'))
