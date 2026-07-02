"""Seed des Rapports Annuels de Performance (rubrique « rapports-performance »).

⚠️ Liste d'institutions reprise du frontend ; liens PDF en « # » — à brancher
via l'admin. Idempotent : ne touche qu'à la rubrique « rapports-performance ».

    python manage.py seed_rap
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from budget.models import DocumentBudget

RUBRIQUE = 'rapports-performance'

INSTITUTIONS = {
    2025: [
        'Comptes Spéciaux',
        "Ministère de l'Urbanisme et de l'Habitat",
        'Ministère de la Santé Publique, de la Population et des Affaires Sociales',
        "Ministère de l'Hydraulique, de l'Assainissement et de l'Environnement",
        "Ministère de l'Éducation Nationale, de l'Alphabétisation, de l'Enseignement Professionnel et de la Promotion",
        'Ministère des Mines',
        "Ministère des Transports et de l'Équipement",
        'Ministère du Pétrole',
        "Ministère de l'Agriculture et de l'Élevage",
        "Ministère du Commerce et de l'Industrie",
        "Ministère de l'Artisanat et du Tourisme",
        "Ministère de l'Action Humanitaire et de la Gestion des Catastrophes",
        "Ministère de l'Économie et des Finances",
        "Ministère de la Fonction Publique, du Travail et de l'Emploi",
        "Ministère de l'Énergie",
        "Ministère de l'Intérieur, de la Sécurité Publique et de l'Administration du Territoire",
        'Secrétariat Général du Gouvernement',
        'Cour des Comptes',
        "Cour d'État",
        "Ministère de la Justice et des Droits de l'Homme",
        'Ministère de la Défense Nationale',
        "Ministère des Affaires Étrangères, de la Coopération et des Nigériens à l'Extérieur",
        'Ministère de la Jeunesse, de la Culture, des Arts et des Sports',
        "Ministère de la Communication, des Postes et de l'Économie Numérique",
        "Ministère de l'Enseignement Supérieur, de la Recherche et de l'Innovation Technologique",
        'Assemblée Nationale',
        'Présidence du Conseil National pour la Sauvegarde de la Patrie',
        'Cabinet du Premier Ministre',
    ],
    2023: [
        'Ministère du Commerce',
        'Ministère des Mines',
        'Ministère des Finances',
        'Ministère des Affaires Étrangères et de la Coopération',
        'Ministère de la Justice',
        "Ministère de l'Équipement",
        "Ministère de l'Enseignement Supérieur et de la Recherche",
        "Ministère de l'Énergie et des Énergies Renouvelables",
        "Ministère de l'Emploi, du Travail et de la Protection Sociale",
        "Ministère de l'Élevage",
        "Ministère de l'Éducation Nationale",
        "Ministère de l'Agriculture",
        'Cabinet du Premier Ministre',
    ],
    2021: [
        'Service du Premier Ministre (PM)',
        "Ministère de l'Agriculture et de l'Élevage",
        'Ministère de la Communication, chargé des Relations avec les Institutions',
        "Ministère de l'Aménagement du Territoire et du Développement Communautaire",
        'Ministère de la Défense Nationale',
        "Ministère de l'Équipement",
        "Ministère de l'Enseignement Supérieur et de la Recherche",
        "Ministère de l'Enseignement Technique et de la Formation Professionnelle",
        "Ministère de l'Emploi, du Travail et de la Protection Sociale",
        "Ministère de l'Hydraulique et de l'Assainissement",
        "Ministère de l'Intérieur et de la Décentralisation",
        'Ministère de la Jeunesse et du Sport',
        "Ministère de la Poste et des Nouvelles Technologies de l'Information",
        'Ministère des Transports',
        "Ministère de l'Urbanisme et du Logement",
    ],
}


class Command(BaseCommand):
    help = "Pré-remplit les Rapports Annuels de Performance (rubrique rapports-performance)."

    @transaction.atomic
    def handle(self, *args, **options):
        DocumentBudget.objects.filter(rubrique=RUBRIQUE).delete()
        total = 0
        for annee, institutions in INSTITUTIONS.items():
            for i, nom in enumerate(institutions):
                DocumentBudget.objects.create(
                    rubrique=RUBRIQUE, annee=annee, titre=nom, type='RAP',
                    lien='#', ordre=i,
                )
                total += 1
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {total} rapports de performance crees (rubrique {RUBRIQUE}).'))
