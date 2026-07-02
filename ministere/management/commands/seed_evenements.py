"""Seed de l'agenda du Ministère (données de démonstration).

⚠️ Événements fictifs — à remplacer par les vrais via l'admin.
Idempotent.

    python manage.py seed_evenements
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from ministere.models import Evenement

# (titre, type, date_debut, date_fin|None, heure, lieu, description, image_url, a_la_une)
EVENEMENTS = [
    ('Conférence budgétaire annuelle 2026', 'Conférence', date(2026, 7, 15), None,
     '09h00 – 17h00', 'Palais des Congrès, Niamey',
     "Présentation des grandes orientations du budget de l'État et concertation avec les "
     "partenaires économiques et sociaux sur les priorités de financement.",
     'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80',
     True),
    ('Atelier de validation du DPPD 2027-2029', 'Atelier', date(2026, 7, 2), None,
     '08h30', 'Ministère des Finances, Niamey',
     "Travaux techniques de validation du Document de Programmation Pluriannuelle des Dépenses "
     "avec les directions sectorielles.",
     '', False),
    ('Mission du FMI — revue du programme', 'Mission', date(2026, 9, 10), date(2026, 9, 20),
     '', 'Niamey',
     "Revue conjointe de la mise en œuvre du programme économique et financier appuyé par le FMI.",
     '', False),
    ('Signature de convention de financement avec la BAD', 'Cérémonie', date(2026, 8, 5), None,
     '11h00', 'Cabinet du Ministre',
     "Cérémonie de signature d'un accord de financement avec la Banque Africaine de Développement "
     "pour des projets d'infrastructures.",
     'https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1200&q=80',
     False),
    ('Forum national sur la mobilisation des recettes', 'Conférence', date(2026, 5, 20), None,
     '09h00', 'Hôtel Radisson Blu, Niamey',
     "Échanges sur les leviers d'élargissement de l'assiette fiscale et la modernisation des régies "
     "financières (DGI, Douanes).",
     '', False),
    ('Réunion du comité de trésorerie', 'Réunion', date(2026, 6, 12), None,
     '15h00', 'Ministère des Finances',
     "Point mensuel sur la situation de trésorerie de l'État et le plan d'engagement des dépenses.",
     '', False),
    ("Atelier sur la dématérialisation (e-SECeF)", 'Atelier', date(2026, 4, 18), None,
     '08h00', 'Direction Générale du Budget',
     "Formation des gestionnaires de crédits à la chaîne dématérialisée de la dépense publique.",
     '', False),
]


class Command(BaseCommand):
    help = "Pré-remplit l'agenda du Ministère (événements de démonstration)."

    @transaction.atomic
    def handle(self, *args, **options):
        Evenement.objects.all().delete()
        for titre, type_, debut, fin, heure, lieu, desc, url, une in EVENEMENTS:
            Evenement.objects.create(
                titre=titre, type=type_, date_debut=debut, date_fin=fin,
                heure=heure, lieu=lieu, description=desc, image_url=url, a_la_une=une,
            )
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(EVENEMENTS)} evenements crees.'))
