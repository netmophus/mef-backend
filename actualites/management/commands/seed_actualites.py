"""Seed des actualités, repris du frontend (NewsHighlights.js).

⚠️ Contenu de démonstration — à remplacer par les vrais articles via l'admin.
Idempotent.

    python manage.py seed_actualites
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from actualites.models import Actualite

# Corps générique de démonstration (un paragraphe par ligne).
CONTENU = (
    "Cette actualité s'inscrit dans la dynamique de l'action du Ministère des Finances, "
    "au service de la transparence et du développement national.\n"
    "Le Ministère réaffirme sa détermination à conduire les réformes prioritaires et à "
    "renforcer la mobilisation des ressources publiques.\n"
    "Les services concernés assureront le suivi de la mise en œuvre, en lien avec "
    "l'ensemble des parties prenantes."
)

# (titre, rubrique, date, chapo, image_url, a_la_une)
ARTICLES = [
    ('Le Ministre des Finances signe de nouveaux accords de financement', 'Activités du Ministre', date(2026, 6, 12),
     'Plusieurs conventions ont été paraphées avec les partenaires pour appuyer les projets prioritaires de développement du pays.',
     'https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1600&q=80', True),
    ("Communication en Conseil des Ministres sur le budget de l'État", 'Événements', date(2026, 6, 10),
     "Le Ministre a présenté l'état d'exécution du budget et les perspectives.",
     'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=1200&q=80', False),
    ('Audience avec la délégation du Fonds Monétaire International', 'Audiences & Rencontres', date(2026, 6, 6),
     'Les échanges ont porté sur la coopération et les réformes en cours.',
     'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&q=80', False),
    ("Discours d'ouverture du forum économique national", 'Activités du Ministre', date(2026, 6, 2),
     "Le Ministre a appelé à la mobilisation de tous pour la relance.",
     'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80', False),
    ('Adoption du projet de loi de finances 2026', 'Événements', date(2026, 5, 28),
     "Le projet de budget a été adopté et sera transmis à l'Assemblée.",
     'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80', False),
    ('Rencontre avec les acteurs du secteur privé national', 'Audiences & Rencontres', date(2026, 5, 21),
     'Le dialogue public-privé au service de la croissance.',
     'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1200&q=80', False),
    ("Visite de terrain : suivi des projets d'investissement", 'Activités du Ministre', date(2026, 5, 14),
     "Le Ministre a constaté l'avancement des chantiers prioritaires.",
     'https://images.unsplash.com/photo-1531545514256-b1400bc00f31?auto=format&fit=crop&w=1200&q=80', False),
    ('Audience avec les partenaires techniques et financiers', 'Audiences & Rencontres', date(2026, 5, 7),
     'Renforcement de la coopération autour des réformes des finances publiques.',
     'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80', False),
    ('Examen du cadrage macroéconomique à moyen terme', 'Événements', date(2026, 4, 29),
     'Les grandes orientations budgétaires pour les prochaines années.',
     'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1200&q=80', False),
    ('Lancement de la campagne de mobilisation des recettes', 'Activités du Ministre', date(2026, 4, 22),
     "Une stratégie renforcée pour élargir l'assiette fiscale.",
     'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80', False),
]


class Command(BaseCommand):
    help = "Pré-remplit les actualités (données de démonstration du frontend)."

    @transaction.atomic
    def handle(self, *args, **options):
        Actualite.objects.all().delete()
        # Les 6 actualités les plus récentes sont mises « à la une ».
        for i, (titre, rubrique, d, chapo, url, une) in enumerate(ARTICLES):
            Actualite.objects.create(
                titre=titre, rubrique=rubrique, date=d, chapo=chapo,
                contenu=CONTENU, image_url=url, a_la_une=(une or i < 6),
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(ARTICLES)} actualites creees.'))
