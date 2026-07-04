"""Seed de démonstration du courrier arrivée.

Crée 3 utilisateurs de démo (BO001, LECT001, AGENT002) et 25 courriers
arrivée réalistes (dont 3 confidentiels et 2 classés sans suite), chacun avec
un PDF d'une page générique (pas de scan réel). Idempotent.

    python manage.py seed_courrier_demo
"""

import hashlib
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from courrier.models import Registre, CompteurRegistre, Correspondant, Courrier, EvenementCourrier
from courrier.services import generer_numero, journaliser

U = get_user_model()

DEMO_USERS = [
    ('BO001', 'Boubacar', 'Oumarou', 'BUREAU_ORDRE', 'Agent du Bureau d\'Ordre'),
    ('LECT001', 'Lecture', 'Centrale', 'LECTURE_COURRIER_CENTRALE', 'Lecture courrier central'),
    ('AGENT002', 'Amadou', 'Diallo', None, 'Agent'),
]
MDP_DEMO = 'Passe@2026'

# (objet, correspondant, confidentiel, classe)
COURRIERS = [
    ("Notification de décaissement au titre de la FEC", 'FMI', True, False),
    ("Transmission du rapport de mission de supervision", 'Banque Mondiale', False, False),
    ("Situation mensuelle des avoirs du Trésor", 'BCEAO', False, False),
    ("Convocation à la réunion du Comité de trésorerie", 'Primature', False, False),
    ("Demande d'informations sur l'exécution budgétaire", 'Présidence de la République', True, False),
    ("Relevé des opérations du mois écoulé", 'BSIC Niger', False, False),
    ("Avis de crédit documentaire", 'SONIBANK', False, False),
    ("Transmission des états financiers annuels", 'DGI (interne)', False, False),
    ("Correspondance diverse", 'Divers', False, True),
    ("Rapport d'assistance technique — finances publiques", 'FMI', False, False),
    ("Accord de financement du projet de résilience", 'Banque Mondiale', False, False),
    ("Note sur la politique monétaire régionale", 'BCEAO', False, False),
    ("Instruction relative aux marchés publics", 'Primature', False, False),
    ("Demande d'audience du Ministre", 'Présidence de la République', False, False),
    ("Relevé de compte courant de l'État", 'BSIC Niger', False, False),
    ("Confirmation de virement international", 'SONIBANK', False, False),
    ("Bordereau de transmission de pièces comptables", 'Trésor National', False, False),
    ("Note confidentielle sur la dette extérieure", 'BCEAO', True, False),
    ("Invitation au séminaire régional UEMOA", 'Banque Mondiale', False, False),
    ("Demande de régularisation de dossier", 'Divers', False, True),
    ("Transmission du projet de loi de finances", 'Primature', False, False),
    ("Rapport trimestriel d'exécution", 'Trésor National', False, False),
    ("Notification de tirage sur prêt", 'FMI', False, False),
    ("Courrier relatif à la mobilisation des recettes", 'DGI (interne)', False, False),
    ("Accusé de réception de documents budgétaires", 'Présidence de la République', False, False),
]


def pdf_demo(texte):
    """Construit un PDF d'une page valide (avec xref) contenant `texte`."""
    texte = ''.join(c for c in texte if 32 <= ord(c) < 127).replace('(', ' ').replace(')', ' ')
    contenu = ("BT /F1 14 Tf 40 120 Td (" + texte + ") Tj ET").encode('latin-1', 'replace')
    objets = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 200] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(contenu)).encode() + b" >>\nstream\n" + contenu + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objets, start=1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    xref_pos = len(out)
    n = len(objets) + 1
    out += b"xref\n0 " + str(n).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += (b"trailer\n<< /Size " + str(n).encode() + b" /Root 1 0 R >>\nstartxref\n"
            + str(xref_pos).encode() + b"\n%%EOF")
    return out


class Command(BaseCommand):
    help = 'Pré-remplit le courrier arrivée (démo) + utilisateurs BO001/LECT001/AGENT002.'

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Utilisateurs de démo (mot de passe connu, pas de changement forcé pour faciliter les tests)
        users = {}
        for matricule, prenom, nom, groupe, fonction in DEMO_USERS:
            u, _ = U.objects.get_or_create(
                matricule=matricule,
                defaults={'first_name': prenom, 'last_name': nom, 'fonction': fonction})
            u.first_name, u.last_name, u.fonction = prenom, nom, fonction
            u.doit_changer_mdp = False
            u.is_active = True
            u.set_password(MDP_DEMO)
            u.save()
            u.groups.clear()
            if groupe:
                u.groups.add(Group.objects.get(name=groupe))
            users[matricule] = u

        bo = users['BO001']

        # 2) Reset des courriers de démo + compteur ARR de l'année
        EvenementCourrier.objects.all().delete()
        Courrier.objects.all().delete()
        arr = Registre.objects.get(code='ARR')
        CompteurRegistre.objects.filter(registre=arr, annee=date.today().year).update(dernier_numero=0)

        # 3) 25 courriers étalés sur ~2 mois
        base = date.today() - timedelta(days=58)
        classes = 0
        for i, (objet, corr_nom, confidentiel, classe) in enumerate(COURRIERS):
            correspondant = Correspondant.objects.get(nom=corr_nom)
            date_arrivee = base + timedelta(days=int(i * 2.3))
            date_document = date_arrivee - timedelta(days=3)
            numero = generer_numero(arr)
            courrier = Courrier(
                registre=arr, numero_ordre=numero, sens='ARRIVEE', enregistre_par=bo,
                date_document=date_document, date_arrivee=date_arrivee,
                correspondant=correspondant, objet=objet,
                confidentialite='CONFIDENTIEL' if confidentiel else 'ORDINAIRE',
                nombre_pieces=1 + (i % 3),
            )
            pdf = pdf_demo(f"Courrier {numero}")
            courrier.hash_sha256 = hashlib.sha256(pdf).hexdigest()
            courrier.scan.save(f'{numero}.pdf', ContentFile(pdf), save=True)
            journaliser(courrier, 'ENREGISTREMENT', bo, {'numero_ordre': numero})
            if classe:
                courrier.statut = 'CLASSE'
                courrier.save(update_fields=['statut'])
                journaliser(courrier, 'CLASSEMENT', bo)
                classes += 1

        conf = sum(1 for *_, c, _ in COURRIERS if c)
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(COURRIERS)} courriers ({conf} confidentiels, {classes} classes) '
            f'+ 3 users demo (mdp {MDP_DEMO}).'))
