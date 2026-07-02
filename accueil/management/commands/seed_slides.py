"""Seed du carrousel d'accueil, identique au frontend actuel (HeroSlider.js).

Idempotent : reconstruit la liste des slides à chaque exécution.
Si le visuel officiel existe dans le frontend (public/slides/), il est
copié dans les médias du backend pour conserver le même rendu.

    python manage.py seed_slides
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from accueil.models import Slide

# Dossier des visuels officiels existants côté frontend.
FRONTEND_SLIDES = Path(settings.BASE_DIR).parent / 'finance-frontend' / 'public' / 'slides'

# Données reprises telles quelles de HeroSlider.js
SLIDES = [
    {
        'categorie': 'Le Ministère',
        'titre': 'Mot du Ministre',
        'texte': "Le Ministre des Finances présente la vision et les priorités du "
                 "Gouvernement pour des finances publiques saines et au service du développement.",
        'image_file': None,  # ministre.jpg pas encore fourni -> secours
        'secours': 'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=1920&q=80',
        'position': 'center top',
        'cta_label': 'Lire le message', 'cta_href': '/le-ministere/ministre', 'cta_icon': 'arrow',
        'cta2_label': '', 'cta2_href': '',
    },
    {
        'categorie': 'République du Niger',
        'titre': 'Ministère des Finances',
        'texte': "Au cœur de Niamey, le Ministère pilote la politique budgétaire, fiscale "
                 "et financière de l'État au service des citoyens.",
        'image_file': 'immeuble-ministere.jpg',  # visuel officiel existant
        'secours': 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1920&q=80',
        'position': 'center',
        'cta_label': 'Découvrir le Ministère', 'cta_href': '/le-ministere', 'cta_icon': 'arrow',
        'cta2_label': '', 'cta2_href': '',
    },
    {
        'categorie': 'Loi de finances',
        'titre': 'Loi de Finances 2025',
        'texte': "Découvrez les grandes orientations budgétaires de l'État et les priorités "
                 "d'investissement pour le développement du Niger.",
        'image_file': None,
        'secours': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1920&q=80',
        'position': '',
        'cta_label': 'Consulter le document', 'cta_href': '/budget/lois-de-finances', 'cta_icon': 'download',
        'cta2_label': 'En savoir plus', 'cta2_href': '/budget',
    },
    {
        'categorie': 'Transparence',
        'titre': "Rapports d'exécution budgétaire",
        'texte': "Suivez l'exécution du budget de l'État en toute transparence, "
                 "trimestre après trimestre.",
        'image_file': None,
        'secours': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1920&q=80',
        'position': '',
        'cta_label': 'Voir les rapports', 'cta_href': '/budget/rapports-execution', 'cta_icon': 'arrow',
        'cta2_label': '', 'cta2_href': '',
    },
    {
        'categorie': 'Services en ligne',
        'titre': 'La fiscalité se modernise',
        'texte': 'Téléprocédures, marchés publics dématérialisés (e-SECeF), DGI en ligne : '
                 'des services plus simples et plus rapides.',
        'image_file': None,
        'secours': 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1920&q=80',
        'position': '',
        'cta_label': 'Accéder aux services', 'cta_href': '/directions/directions-generales', 'cta_icon': 'arrow',
        'cta2_label': '', 'cta2_href': '',
    },
]


class Command(BaseCommand):
    help = "Pré-remplit le carrousel d'accueil avec les slides actuels du frontend."

    @transaction.atomic
    def handle(self, *args, **options):
        Slide.objects.all().delete()
        copies = 0
        for i, s in enumerate(SLIDES):
            slide = Slide(
                categorie=s['categorie'], titre=s['titre'], texte=s['texte'],
                secours=s['secours'], position=s['position'],
                cta_label=s['cta_label'], cta_href=s['cta_href'], cta_icon=s['cta_icon'],
                cta2_label=s['cta2_label'], cta2_href=s['cta2_href'],
                ordre=i,
            )
            nom_fichier = s['image_file']
            if nom_fichier:
                source = FRONTEND_SLIDES / nom_fichier
                if source.exists():
                    with source.open('rb') as f:
                        slide.image.save(nom_fichier, File(f), save=False)
                    copies += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ! visuel introuvable, secours utilise : {source}'))
            slide.save()

        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(SLIDES)} slides crees ({copies} image(s) officielle(s) copiee(s)).'))
