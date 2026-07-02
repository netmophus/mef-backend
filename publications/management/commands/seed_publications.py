"""Seed des publications (3 rubriques), repris du frontend.

⚠️ Liens PDF en « # » — à brancher via l'admin. Idempotent.

    python manage.py seed_publications
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from publications.models import Publication

# (type, titre)
MINISTERE = [
    ('Bulletin', 'Bulletin Statistique sur la Dette Publique - fin décembre 2025'),
    ('Arrêté', "Arrêté n°0148_MEF_SG_DGB du 30 avril 2026 modifiant et complétant l'arrêté n°089-MEF-SG-DGB du 25 mars 2026_Comité PEG"),
    ('Document', 'Document de Programmation Budgétaire et Économique Pluriannuelle 2026-2028 (Mai 2025)'),
    ('Arrêté', "Arrêté n°00087/MDPM/F/SG/DGB du 25 mars 2026 DDRB Comité d'élaboration du Document de Déclaration sur les Risques budgétaires"),
    ('Arrêté', "Arrêté n°00089 du 25 mars 2026 Comité de pilotage du Plan d'Engagement Global"),
    ('Compte rendu', "COMPTE RENDU D'ADJUDICATION DES OBLIGATIONS ASSIMILABLES DU TRÉSOR"),
    ('Décret', 'Décret n°2025-703-PRN-MEF du 28 novembre 2025, modifiant et complétant le décret n°2023-179-CNSP-MEF du 14 octobre 2023, portant organisation du MEF'),
    ('Décret', 'Décret n°2024-567-P-CNSP-MEF du 19 septembre 2024, modifiant et complétant le décret n°2023-179 du MEF du 14 octobre 2023, portant organisation du MEF'),
    ('Synthèse', "Synthèse de l'Étude de Vulnérabilité du Projet de Renforcement de l'Alimentation en Eau Potable et Assainissement et d'Amélioration de la Résilience à Zinder, Mirriah et Villages Environnants (PREPAAR-ZMVE)"),
    ('Synthèse', "Synthèse de l'Étude de Vulnérabilité du Projet de Connectivité et d'Intégration du Sud du Niger (PICSN)"),
    ('Synthèse', "Synthèse de l'Étude de Vulnérabilité du Projet d'Appui au Développement des Cultures Irriguées et à l'Intensification de la Production Animale (PACIPA)"),
    ('Rapport', 'Rapport Analyse de la Viabilité de la Dette_AVD_2025'),
    ('Bulletin', 'Bulletin statistique sur la Dette Publique fin septembre 2025'),
    ('Bulletin', 'Bulletin statistique annuel 2024 sur la dette publique'),
    ('Plan', "Plan d'Engagement Environnemental et Social (PEES) - Version corrigée - 8 mai 2025"),
]

AUTRES = [
    ('Plan', "Plan d'Engagement Environnemental et Social (PEES) - 04 février 2026"),
    ('Plan', 'Environmental and Social Commitment Plan (ESCP) - 04 February 2026'),
    ('Communiqué', 'Communication du Ministre Délégué au Budget au Conseil Consultatif de la Refondation sur la situation économique et financière — Décembre 2025'),
    ('Étude', "Mission d'évaluation virtuelle du projet d'aménagement et bitumage de la route Doutchi-Kurdula – frontière du Nigeria, 20-22 septembre 2021"),
    ('Étude', "Étude d'impact environnemental et social du projet d'aménagement et de bitumage de la route Dogondoutchi – Bagaroua (140,475 km) - Rapport définitif"),
    ('Rapport', 'Rapport provisoire de faisabilité économique : Doutchi - Dogonkiria - Bagaroua'),
    ('Rapport', 'Rapport économique - Annexe TRE : Doutchi - Bagaroua'),
    ('Projet', "Projet de renforcement de la résilience des communautés rurales à l'insécurité alimentaire et nutritionnelle au Niger (PRECIS) - Rapport de conception détaillée"),
    ('Projet', 'Programme de gestion du secteur public pour la résilience et la prestation de services (P174822)'),
    ('Projet', "Projet d'approfondissement du secteur financier et d'inclusion financière au Niger (PASFIF – Niger)"),
    ('Étude', "Études de faisabilité économique, études d'impacts environnemental et social, études techniques détaillées avec production du dossier d'appel d'offres (DAO) pour les travaux de réhabilitation de la route Tahoua-Tamaya (205 km)"),
    ('Projet', "Niger, Projet d'Amélioration de l'Accès des Femmes et des Filles aux Services de Santé et de Nutrition dans les Zones Prioritaires - LAFIA-IYALI (Phase 1) (P171767)"),
    ('Projet', 'Projet Intégré de Développement Urbain et de Résilience Multisectorielle au Niger (PIDUREM)'),
    ('Projet', "Projet Régional d'Appui au Pastoralisme au Sahel – Phase II (PRAPS 2) - Document de Pré PAD"),
    ('Projet', "Projet Intégré de Désenclavement des Zones de Production Transfrontalières Hamdara-Wacha-Dungass-Frontière Nigeria - Rapport d'Évaluation du Projet"),
    ('Communiqué', "Recrutement d'un/une (01) Responsable de Sécurité du Système d'Information (RSSI) et d'un (01) Auditeur Senior"),
    ('Décret', "Décret n°2023-179_PCNSP_MEF du 14 octobre 2023 portant organisation du Ministère de l'Économie et des Finances"),
    ('Rapport', 'Rapport du Marché Nigérien des Assurances au titre de 2022'),
    ('Communiqué', "Centre Professionnel de Formation à l'Assurance (CPFA) : Communiqué"),
    ('FMI', "Le conseil d'administration du FMI achève la deuxième revue de l'accord au titre de la facilité élargie de crédit (FEC) en faveur du Niger"),
    ('Communiqué', 'SNFI : Appel à candidatures'),
    ('Document', 'Système de gestion environnementale et sociale du FDIF (Fonds de Développement de la Finance Inclusive)'),
    ('Arrêté', 'Arrêté n°0074-MF-SG-DGB du 15-02-2022 portant organisation de la DGB et fixant les attributions des responsables'),
    ('Arrêté', "Arrêté n°0368_MF_SG_DGEP_PE du 29 juin 2022 déterminant la liste des Établissements Publics, des Sociétés d'État et des Sociétés d'Économie Mixte"),
    ('Décret', 'Décret n°2022-459_PRN_MF du 02 juin 2022 modifiant et complétant le décret n°327-PRN-MF du 13 mai 2021 portant organisation du Ministère des Finances'),
    ('FMI', 'FMI - Perspectives économiques régionales - Afrique subsaharienne : Un nouveau choc et une faible marge de manœuvre - Présentation du 10 juin 2022'),
    ('FMI', 'FMI - Perspectives économiques régionales - Afrique subsaharienne : Un nouveau choc et une faible marge de manœuvre'),
    ('FMI', 'Communiqué de presse mission FMI - mai 2022'),
    ('Arrêté', 'Arrêté N°000145/MF/SG/DGT/CP du 28 mars 2022 portant organisation de la Direction Générale du Trésor et de la Comptabilité Publique et fixant les attributions des responsables'),
    ('Communiqué', 'Communiqué relatif au recrutement des Cadres Supérieurs, gestionnaires et comptables à la CICA-Ré'),
    ('Document', 'Document de Programmation Budgétaire et Économique Pluriannuelle (DPBEP 2022-2024)'),
    ('Communiqué', "Communiqué relatif à la fermeture de l'accès au rond justice venant du siège de la banque BSIC"),
    ('Loi', 'Loi N° 2019-56 portant organisation de la concurrence au Niger'),
    ('Loi', 'Loi n° 2019-50 déterminant les infractions et leurs sanctions en matière de protection des consommateurs'),
    ('Loi', "Ordonnance N° 2020-02 du 27 janvier 2020 déterminant la liste des autres agents publics assujettis à l'obligation de déclaration de biens"),
    ('Plan', "Plan Prévisionnel de Passation des Marchés Publics du Ministère des Finances au titre de l'année 2020"),
    ('Document', 'Liste des contribuables à jour dans leurs obligations'),
    ('Communiqué', "Les résultats du concours international d'entrée au CPFA (Centre Professionnel de Formation en Assurance) du Niger"),
    ('Rapport', "Rapport d'évaluation de la campagne agricole d'hivernage 2018 et perspectives alimentaires 2018/2019"),
    ('Document', "Document-cadre de politique et de stratégie régionale d'inclusion financière dans l'UEMOA"),
    ('FMI', "Perspectives économiques régionales : Afrique subsaharienne, Un changement de cap s'impose (FMI 2016)"),
    ('Document', "Recueil des textes fondamentaux de la réglementation des marchés publics et des délégations de service public & les directives de l'UEMOA"),
]

ENT_2020 = ['SPEN', 'SOPAMIN', 'SONIDEP', 'ORTN', 'OPVN', 'ONPPC', 'NIGER TELECOMS', 'NIGELEC', 'LONANI', 'CNUT']
ENT_2018 = ['SOPAMIN', 'SONIDEP', 'NIGER TELECOMS', 'NIGELEC', 'LONANI']
ETATS = (
    [('2020', f'État financier certifié synthétisé au 31 décembre 2020 — {e}') for e in ENT_2020]
    + [('2018', f'États financiers 2018 — {e}') for e in ENT_2018]
)

RUBRIQUES = {
    'ministere': MINISTERE,
    'autres': AUTRES,
    'etats-financiers': ETATS,
}


class Command(BaseCommand):
    help = 'Pré-remplit les publications (3 rubriques, démo).'

    @transaction.atomic
    def handle(self, *args, **options):
        Publication.objects.all().delete()
        total = 0
        for rubrique, items in RUBRIQUES.items():
            for i, (type_, titre) in enumerate(items):
                Publication.objects.create(
                    rubrique=rubrique, type=type_, titre=titre, lien='#', ordre=i,
                )
                total += 1
        self.stdout.write(self.style.SUCCESS(f'[OK] {total} publications creees.'))
