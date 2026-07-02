"""Seed de l'Historique (dénominations, ministres, délégués, textes d'organisation).

⚠️ Données reprises du frontend ; photos/PDF à brancher via l'admin. Idempotent.

    python manage.py seed_historique
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from ministere.models import Denomination, MinistreHistorique, TexteOrganisation

DENOMINATIONS = [
    ('1952', 'Direction Locale des Finances'),
    ('1958', 'Ministère des Finances'),
    ('1965', 'Ministère des Affaires Économiques et des Finances'),
    ('1970', 'Ministère des Affaires Économiques et des Finances, des Affaires Sahariennes et Nomades'),
    ('1974', 'Ministère des Finances'),
    ('1991', "Ministère de l'Économie et des Finances"),
    ('1994', 'Ministère des Finances et du Plan'),
    ('1996', "Ministère de l'Économie, des Finances et du Plan, puis Ministère des Finances"),
    ('1997', "Ministère de l'Économie et des Finances, puis des Réformes et de la Privatisation"),
    ('1999', 'Ministère des Finances et des Réformes Économiques'),
    ('2000', 'Ministère des Finances'),
    ('2002', "Ministère de l'Économie et des Finances"),
    ('2011', 'Ministère des Finances'),
    ('2015', "Ministère de l'Économie et des Finances"),
    ('2016', 'Ministère des Finances'),
    ('Depuis 2023', "Ministère de l'Économie et des Finances"),
]

# (nom, desc, photo_url, secours)
MINISTRES = [
    ('Dr Maman Laouali ABDOU RAFA', "Ministre de l'Économie et des Finances (en exercice).", '/DrRafa.jpeg', ''),
    ('M. Ahmat Jidoud', 'Ministre des Finances du 07/04/2021 au 26 juillet 2023.', '/ministres/ahmat-jidoud.jpg', 'https://images.unsplash.com/photo-1568602471122-7832951cc4c5?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', 'Ministre des Finances · 2016 – 2021.', '', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', 'Ministre des Finances · 2011 – 2016.', '', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', 'Ministre des Finances · 2002 – 2011.', '', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', 'Ministre des Finances · 1991 – 2002.', '', 'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=600&q=80'),
]

DELEGUES = [
    ('— À renseigner —', 'Ministre délégué au Budget · période à renseigner.', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', "Secrétaire d'État au Budget · période à renseigner.", 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', "Secrétaire d'État aux Finances · période à renseigner.", 'https://images.unsplash.com/photo-1568602471122-7832951cc4c5?auto=format&fit=crop&w=600&q=80'),
    ('— À renseigner —', 'Ministre délégué · période à renseigner.', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80'),
]

# (titre, annee)
TEXTES = [
    ("Décret n°2023-179/PCNSP/MEF du 14 octobre 2023 portant organisation du Ministère de l'Économie et des Finances", '2023'),
    ("Décret n°2023-191/PRN/MF du 23 février 2023 modifiant et complétant le décret n°2021-327/PRN/MF du 13 mai 2021, portant organisation du Ministère des Finances (modifié par le décret n°2022-459/PRN/MF du 02 juin 2022)", '2023'),
    ("Décret n°2023-191/PRN/MF du 23 février 2023 modifiant et complétant le décret n°2021-327/PRN/MF du 13 mai 2021, portant organisation du MF", '2023'),
    ("Décret n°2022-459/PRN/MF du 02 juin 2022 modifiant et complétant le décret n°327/PRN/MF du 13 mai 2021 portant organisation du Ministère des Finances", '2022'),
    ("Décret n°2021-327/PRN/MF du 13 mai 2021 portant organisation du Ministère des Finances", '2021'),
    ("Décret n°2019-598/PRN/MF du 18 octobre 2019 modifiant et complétant le décret n°2018-497/PRN/MF du 20 juillet 2018, portant organisation du Ministère des Finances", '2019'),
    ("Décret n°2018-497/PRN/MF du 20 juillet 2018 portant organisation du Ministère des Finances", '2018'),
]


class Command(BaseCommand):
    help = "Pré-remplit l'Historique du Ministère (données de démonstration)."

    @transaction.atomic
    def handle(self, *args, **options):
        Denomination.objects.all().delete()
        MinistreHistorique.objects.all().delete()
        TexteOrganisation.objects.all().delete()

        for i, (an, nom) in enumerate(DENOMINATIONS):
            Denomination.objects.create(an=an, nom=nom, ordre=i)
        for i, (nom, desc, photo_url, secours) in enumerate(MINISTRES):
            MinistreHistorique.objects.create(categorie='ministre', nom=nom, description=desc,
                                              photo_url=photo_url, secours=secours, ordre=i)
        for i, (nom, desc, secours) in enumerate(DELEGUES):
            MinistreHistorique.objects.create(categorie='delegue', nom=nom, description=desc,
                                              secours=secours, ordre=i)
        for i, (titre, annee) in enumerate(TEXTES):
            TexteOrganisation.objects.create(titre=titre, annee=annee, lien='#', ordre=i)

        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(DENOMINATIONS)} denominations, {len(MINISTRES)} ministres, '
            f'{len(DELEGUES)} delegues, {len(TEXTES)} textes.'))
