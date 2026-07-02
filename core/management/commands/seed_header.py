"""Seed des données de l'en-tête, identiques au frontend actuel.

Reprend EXACTEMENT :
  - les coordonnées/identité de `src/config.js` et `MainMenu.js`
  - le menu de `src/components/menuConfig.js`

Idempotent : relançable sans créer de doublons (le menu est reconstruit).

    python manage.py seed_header
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import SiteConfig, MenuItem


# Identité + coordonnées (config.js / MainMenu.js)
SITE = {
    'nom': 'MINISTÈRE DES FINANCES',
    'sous_titre': 'République du Niger',
    'telephone': '+227 20 72 23 47',
    'email': 'finances@finances.gov.ne',
    'adresse': 'Avenue des ministères, BP 389 — Niamey Plateau',
    'facebook': 'https://facebook.com',
    'twitter': 'https://x.com',
    'youtube': 'https://youtube.com',
}

# Menu de navigation (menuConfig.js) : (label, path, [sous-entrées])
MENU = [
    ('Accueil', '/', []),
    ('Le Ministère', '', [
        ('Le Ministre', '/le-ministere/ministre'),
        ('Historique', '/le-ministere/historique'),
        ('Organigramme', '/le-ministere/organigramme'),
        ('Partenaires', '/le-ministere/partenaires'),
        ('Annuaire', '/le-ministere/annuaire'),
    ]),
    ('Budget', '', [
        ('Lois de finances', '/budget/lois-de-finances'),
        ('Lois de règlement', '/budget/lois-de-reglement'),
        ("Rapports d'exécution", '/budget/rapports-execution'),
        ('Réformes budgétaires', '/budget/reformes-budgetaires'),
        ('Rapports Annuels de Performance', '/budget/rapports-performance'),
        ('Programmation pluriannuelle (DPPD)', '/budget/dppd'),
    ]),
    ('Actualités', '', [
        ('Actualités à la une', '/actualites/a-la-une'),
        ('Revue de presse', '/actualites/revue-de-presse'),
    ]),
    ('Médiathèque', '', [
        ('Photos', '/mediatheque/photos'),
        ('Vidéos', '/mediatheque/videos'),
    ]),
    ('Publications', '', [
        ('Publications du Ministère', '/publications/ministere'),
        ('Autres publications', '/publications/autres'),
        ('États Financiers', '/publications/etats-financiers'),
    ]),
]


class Command(BaseCommand):
    help = "Pré-remplit l'en-tête (configuration du site + menu) avec les données actuelles."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Configuration du site (singleton)
        config = SiteConfig.load()
        for champ, valeur in SITE.items():
            setattr(config, champ, valeur)
        config.save()
        self.stdout.write(self.style.SUCCESS('[OK] Configuration du site enregistree.'))

        # 2. Menu : on repart d'une base propre puis on recrée tout.
        MenuItem.objects.all().delete()
        for i, (label, path, enfants) in enumerate(MENU):
            parent = MenuItem.objects.create(label=label, path=path, ordre=i)
            for j, (sous_label, sous_path) in enumerate(enfants):
                MenuItem.objects.create(label=sous_label, path=sous_path, parent=parent, ordre=j)
        self.stdout.write(self.style.SUCCESS(f'[OK] Menu reconstruit ({len(MENU)} rubriques).'))

        self.stdout.write(self.style.SUCCESS("Seed de l'en-tete termine."))
