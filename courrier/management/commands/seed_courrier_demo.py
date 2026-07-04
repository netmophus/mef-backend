"""Seed de démonstration du courrier (arrivée + imputations C2).

Crée les directions sur 3 niveaux sous DGB, les utilisateurs de démo, 25
courriers arrivée (PDF générique) et un scénario d'imputations pré-joué
montrant tous les états. Idempotent. Réservé au développement (DEBUG=True).

    python manage.py seed_courrier_demo
"""

import hashlib
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comptes.models import Direction
from courrier.models import Registre, CompteurRegistre, Correspondant, Courrier, EvenementCourrier
from courrier.services import (
    generer_numero, journaliser, creer_imputation, accuser_imputation, traiter_imputation,
)

U = get_user_model()
MDP_DEMO = 'Passe@2026'

# (matricule, prénom, nom, groupe|None, fonction, sigle_direction|None)
DEMO_USERS = [
    ('BO001', 'Boubacar', 'Oumarou', 'BUREAU_ORDRE', "Agent du Bureau d'Ordre", None),
    ('LECT001', 'Lecture', 'Centrale', 'LECTURE_COURRIER_CENTRALE', 'Lecture courrier central', None),
    ('AGENT002', 'Amadou', 'Diallo', None, 'Agent', None),
    ('SECSG01', 'Salif', 'Gambo', 'IMPUTATION_CENTRALE', 'Secrétariat du SG', 'SG'),
    ('SECDGB01', 'Sanata', 'Baré', 'SECRETARIAT', 'Secrétariat DGB', 'DGB'),
    ('SECDBE01', 'Boureima', 'Elhadji', 'SECRETARIAT', "Secrétariat DBE", 'DBE'),
    ('SECDIV01', 'Idrissa', 'Diori', 'SECRETARIAT', 'Secrétariat Division des dépenses', 'DIVDEP'),
]

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
    help = 'Pré-remplit le courrier (arrivée + imputations) pour la démo.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_courrier_demo est réservé au développement (DEBUG=True).')

        # 1) Directions 3 niveaux sous DGB
        dgb = Direction.objects.get(sigle='DGB')
        dbe, _ = Direction.objects.get_or_create(
            sigle='DBE', defaults={'nom': "Direction du Budget de l'État", 'parent': dgb, 'ordre': 20})
        divdep, _ = Direction.objects.get_or_create(
            sigle='DIVDEP', defaults={'nom': 'Division des dépenses', 'parent': dbe, 'ordre': 21})

        # 2) Utilisateurs de démo
        users = {}
        for matricule, prenom, nom, groupe, fonction, sigle in DEMO_USERS:
            direction = Direction.objects.get(sigle=sigle) if sigle else None
            u, _ = U.objects.get_or_create(matricule=matricule, defaults={'first_name': prenom})
            u.first_name, u.last_name, u.fonction, u.direction = prenom, nom, fonction, direction
            u.doit_changer_mdp = False
            u.is_active = True
            u.set_password(MDP_DEMO)
            u.save()
            u.groups.clear()
            if groupe:
                u.groups.add(Group.objects.get(name=groupe))
            users[matricule] = u

        bo = users['BO001']

        # 3) Reset courriers + compteur ARR
        EvenementCourrier.objects.all().delete()
        Courrier.objects.all().delete()
        arr = Registre.objects.get(code='ARR')
        CompteurRegistre.objects.filter(registre=arr, annee=date.today().year).update(dernier_numero=0)

        # 4) 25 courriers
        base = date.today() - timedelta(days=58)
        for i, (objet, corr_nom, confidentiel, classe) in enumerate(COURRIERS):
            correspondant = Correspondant.objects.get(nom=corr_nom)
            date_arrivee = base + timedelta(days=int(i * 2.3))
            numero = generer_numero(arr)
            c = Courrier(
                registre=arr, numero_ordre=numero, sens='ARRIVEE', enregistre_par=bo,
                date_document=date_arrivee - timedelta(days=3), date_arrivee=date_arrivee,
                correspondant=correspondant, objet=objet,
                confidentialite='CONFIDENTIEL' if confidentiel else 'ORDINAIRE',
                nombre_pieces=1 + (i % 3))
            pdf = pdf_demo(f'Courrier {numero}')
            c.hash_sha256 = hashlib.sha256(pdf).hexdigest()
            c.scan.save(f'{numero}.pdf', ContentFile(pdf), save=True)
            journaliser(c, 'ENREGISTREMENT', bo, {'numero_ordre': numero})
            if classe:
                c.statut = 'CLASSE'
                c.save(update_fields=['statut'])
                journaliser(c, 'CLASSEMENT', bo)

        # 5) Scénario d'imputations pré-joué (5 courriers ordinaires)
        secsg, secdgb, secdbe = users['SECSG01'], users['SECDGB01'], users['SECDBE01']
        cs = list(Courrier.objects.filter(confidentialite='ORDINAIRE', statut='ENREGISTRE').order_by('id')[:5])
        if len(cs) == 5:
            c1, c2, c3, c4, c5 = cs
            # c1 : imputé DGB, à accuser
            creer_imputation(c1, direction_cible=dgb, instruction='POUR_TRAITEMENT', delai=None, commentaire='', impute_par=secsg)
            # c2 : imputé + accusé (en cours)
            i2 = creer_imputation(c2, direction_cible=dgb, instruction='POUR_TRAITEMENT', delai=None, commentaire='', impute_par=secsg)
            accuser_imputation(i2, secdgb)
            # c3 : cascade sur 3 niveaux DGB -> DBE -> Division des dépenses
            i3 = creer_imputation(c3, direction_cible=dgb, instruction='POUR_ATTRIBUTION', delai=None, commentaire='', impute_par=secsg)
            accuser_imputation(i3, secdgb)
            i3b = creer_imputation(c3, direction_cible=dbe, instruction='POUR_ATTRIBUTION', delai=None, commentaire='', impute_par=secdgb, imputation_mere=i3)
            accuser_imputation(i3b, secdbe)
            creer_imputation(c3, direction_cible=divdep, instruction='POUR_TRAITEMENT', delai=None, commentaire='Traitement division', impute_par=secdbe, imputation_mere=i3b)
            # c4 : imputé avec délai dépassé + accusé
            i4 = creer_imputation(c4, direction_cible=dgb, instruction='POUR_AVIS', delai=date.today() - timedelta(days=5), commentaire='', impute_par=secsg)
            accuser_imputation(i4, secdgb)
            # c5 : imputé + accusé + traité
            i5 = creer_imputation(c5, direction_cible=dgb, instruction='POUR_TRAITEMENT', delai=None, commentaire='', impute_par=secsg)
            accuser_imputation(i5, secdgb)
            traiter_imputation(i5, secdgb, f'Réponse transmise le {date.today():%d/%m/%Y}')

        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(COURRIERS)} courriers + scenario imputations (5) + {len(DEMO_USERS)} users demo.'))
