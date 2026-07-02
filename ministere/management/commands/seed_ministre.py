"""Seed du bloc « Le Ministre », identique au frontend (MinisterCard.js).

Copie la photo officielle depuis public/DrRafa.jpeg si elle existe.
Idempotent.

    python manage.py seed_ministre
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from ministere.models import Ministre, MinistreLien, MinistreRepere, MinistreParcours

FRONTEND_PUBLIC = Path(settings.BASE_DIR).parent / 'finance-frontend' / 'public'
PHOTO_FICHIER = 'DrRafa.jpeg'

MINISTRE = {
    'nom': 'Dr Maman Laouali ABDOU RAFA',
    'fonction': "Ministre de l'Économie et des Finances",
    'etiquette': 'Le Ministre',
    # Biographie (page /le-ministere/ministre)
    'nom_complet': 'Docteur Maman Laouali ABDOU RAFA',
    'presentation_accroche': "Macroéconomiste et spécialiste de la finance, Docteur en "
        "Administration des Affaires (DBA), option Finance, et doctorant en sciences économiques.",
    'presentation_corps': "Haut responsable public, il totalise plus de vingt ans d'expérience "
        "dans la conception, la mise en œuvre et le pilotage des politiques économiques, "
        "financières et budgétaires : stabilité macroéconomique, soutenabilité de la dette "
        "publique, réformes des finances publiques, gouvernance économique et coopération "
        "financière internationale.",
    'conseils_periode': '2016 – 2021',
    'experience': "\n".join([
        "Son expérience en banque centrale, acquise à la BCEAO de 2005 à 2023, a porté sur le "
        "suivi macroéconomique, les statistiques monétaires et de balance des paiements, les "
        "finances publiques, la stabilité financière et bancaire, et l'appui aux politiques "
        "économiques nationales.",
        "Il a bénéficié d'une formation continue approfondie (2004-2025) auprès de la BCEAO, du "
        "FMI, de la Banque mondiale, de la CEDEAO, d'AFRITAC, de l'IDEP et d'universités "
        "internationales (HEC Montréal/UCLA, OMNES Education, London School of Economics).",
        "Auteur de plusieurs travaux de recherche : microfinance, performance financière, "
        "pauvreté et politiques publiques, économie du bien-être en monopoles naturels, "
        "privatisation et endettement.",
    ]),
    'conseils': "\n".join([
        'BCEAO', 'BOAD', 'BIDC', 'BIA Niger', 'BSIC Niger', 'BAGRI', 'FISAN',
        'NIGELEC', 'NIGERTELECOM', 'SOMAIR', 'COMINAK', 'LONANI', 'CAIMA',
    ]),
}

# (label, icône, href) — repris de MinisterCard.js
LIENS = [
    ('Biographie du Ministre', 'menu_book', '/le-ministere/ministre'),
    ('Cabinet du ministre', 'groups', '/le-ministere/cabinet'),
    ('Discours', 'record_voice_over', '/le-ministere/discours'),
]

# (icône, texte) — repères de la page biographie
REPERES = [
    ('cake', 'Né le 1ᵉʳ mai 1975 à Tessaoua (Maradi)'),
    ('family', 'Marié, père de 7 enfants'),
    ('translate', 'Haoussa · Français · Anglais · Djerma'),
]

# (catégorie, période, titre, détail)
FORMATION = [
    ('formation', '2022 – 2025', 'Doctorate in Business Administration (DBA) — Finance', 'Paris Panthéon-Assas / IFG — Très Bien'),
    ('formation', '2001 – 2003', 'DEA en sciences économiques (PTCI, 8ᵉ prom.)', 'Univ. de Ouagadougou — Major, Très Bien'),
    ('formation', '2000 – 2001', 'Maîtrise en sciences économiques', 'Univ. de Ouagadougou — Vice-major'),
    ('formation', '1996 – 1999', 'Licence en sciences économiques', 'Univ. de Ouagadougou'),
]
PARCOURS = [
    ('professionnel', 'Juil. 2023 – Fév. 2026', 'Directeur national de la BCEAO pour le Niger', 'BCEAO'),
    ('professionnel', 'Fév. 2022 – Juin 2023', 'Conseiller du Directeur national', 'BCEAO'),
    ('professionnel', 'Avr. – Oct. 2021', 'Secrétaire général', 'Ministère des Finances'),
    ('professionnel', 'Janv. 2020 – Avr. 2021', 'Secrétaire général adjoint', 'Ministère des Finances'),
    ('professionnel', 'Sept. 2016 – Janv. 2020', 'DG des opérations financières et des réformes', 'Ministère des Finances'),
    ('professionnel', 'Sept. 2015 – Oct. 2021', 'Secrétaire permanent du CISPEE/NAB', 'Cabinet du Premier Ministre'),
]


class Command(BaseCommand):
    help = "Pré-remplit le bloc « Le Ministre » avec les données actuelles du frontend."

    @transaction.atomic
    def handle(self, *args, **options):
        ministre = Ministre.load()
        for champ, valeur in MINISTRE.items():
            setattr(ministre, champ, valeur)

        source = FRONTEND_PUBLIC / PHOTO_FICHIER
        if source.exists():
            with source.open('rb') as f:
                ministre.photo.save(PHOTO_FICHIER, File(f), save=False)
            photo_msg = '1 photo copiee'
        else:
            photo_msg = f'photo introuvable ({source}) -> aucune'
        ministre.save()

        MinistreLien.objects.all().delete()
        for i, (label, icone, href) in enumerate(LIENS):
            MinistreLien.objects.create(label=label, icone=icone, href=href, ordre=i)

        ministre.reperes.all().delete()
        for i, (icone, texte) in enumerate(REPERES):
            MinistreRepere.objects.create(ministre=ministre, icone=icone, texte=texte, ordre=i)

        ministre.parcours.all().delete()
        for i, (cat, periode, titre, detail) in enumerate(FORMATION + PARCOURS):
            MinistreParcours.objects.create(
                ministre=ministre, categorie=cat, periode=periode, titre=titre, detail=detail, ordre=i)

        self.stdout.write(self.style.SUCCESS(
            f'[OK] Ministre + biographie enregistres ({photo_msg}) : '
            f'{len(LIENS)} liens, {len(REPERES)} reperes, '
            f'{len(FORMATION)} formations, {len(PARCOURS)} etapes de parcours.'))
