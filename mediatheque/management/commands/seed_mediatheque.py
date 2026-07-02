"""Seed de la médiathèque (photos + vidéos), repris du frontend.

⚠️ Visuels Unsplash de démo — à remplacer par les vrais fichiers via l'admin.
Idempotent.

    python manage.py seed_mediatheque
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from mediatheque.models import Photo, Video

# (titre, url) — repris de data/galeriePhotos.js
PHOTOS = [
    ("Signature d'accords de financement", 'https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=900&q=80'),
    ('Conseil des Ministres', 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=900&q=80'),
    ('Audience avec le FMI', 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=900&q=80'),
    ('Forum économique national', 'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=900&q=80'),
    ('Rencontre avec le secteur privé', 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=900&q=80'),
    ('Cérémonie officielle', 'https://images.unsplash.com/photo-1531545514256-b1400bc00f31?auto=format&fit=crop&w=900&q=80'),
    ('Visite de terrain', 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=900&q=80'),
    ('Partenaires techniques et financiers', 'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=900&q=80'),
]

# (titre, date, duree, miniature_url)
VIDEOS = [
    ('Présentation de la Loi de Finances 2025', date(2026, 6, 12), '4:35', 'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=800&q=80'),
    ('Conférence de presse du Ministre des Finances', date(2026, 6, 6), '8:12', 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=800&q=80'),
    ("Cérémonie de signature d'accords de financement", date(2026, 6, 2), '3:48', 'https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=800&q=80'),
    ("Forum économique national — séance d'ouverture", date(2026, 5, 28), '6:20', 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=800&q=80'),
    ('Audience avec les partenaires techniques et financiers', date(2026, 5, 21), '5:02', 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=800&q=80'),
    ('Lancement de la campagne de mobilisation des recettes', date(2026, 5, 14), '2:57', 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80'),
]


class Command(BaseCommand):
    help = 'Pré-remplit la médiathèque (photos + vidéos de démonstration).'

    @transaction.atomic
    def handle(self, *args, **options):
        Photo.objects.all().delete()
        Video.objects.all().delete()
        for i, (titre, url) in enumerate(PHOTOS):
            Photo.objects.create(titre=titre, image_url=url, ordre=i)
        for i, (titre, d, duree, url) in enumerate(VIDEOS):
            Video.objects.create(titre=titre, date=d, duree=duree, miniature_url=url, lien='#', ordre=i)
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(PHOTOS)} photos + {len(VIDEOS)} videos creees.'))
