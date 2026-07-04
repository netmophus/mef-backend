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
from django.utils import timezone

from comptes.models import Direction
from courrier.models import Registre, CompteurRegistre, Correspondant, Courrier, EvenementCourrier, Imputation
from courrier.services import (
    generer_numero, journaliser, creer_imputation, accuser_imputation, traiter_imputation,
    creer_depart, expedier_courrier, decharger_courrier,
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

        # 5) Scénario d'imputations pré-joué — pilotage (lot C3)
        #    Réparti sur 5 DG pour un tableau « par direction » parlant, avec
        #    retards (2/7/15 j), délais proches, relance d'hier et confidentiel.
        secsg, secdgb, secdbe = users['SECSG01'], users['SECDGB01'], users['SECDBE01']
        dgi = Direction.objects.get(sigle='DGI')
        dgd = Direction.objects.get(sigle='DGD')
        dgtcp = Direction.objects.get(sigle='DGTCP')
        dgep = Direction.objects.get(sigle='DGEP')

        pool_ord = list(Courrier.objects.filter(statut='ENREGISTRE', confidentialite='ORDINAIRE').order_by('id'))
        pool_conf = list(Courrier.objects.filter(statut='ENREGISTRE', confidentialite='CONFIDENTIEL').order_by('id'))

        def j(n):
            return date.today() + timedelta(days=n)

        def scenario(direction, *, instruction='POUR_TRAITEMENT', delai=None, accuse_by=None,
                     impute_il_y_a=1, relance_hier=False, traiter_by=None, confidentiel=False):
            """Crée une imputation de 1er niveau puis antidate son historique."""
            c = (pool_conf if confidentiel else pool_ord).pop(0)
            imp = creer_imputation(c, direction_cible=direction, instruction=instruction,
                                   delai=delai, commentaire='', impute_par=secsg)
            upd = {'date_imputation': timezone.now() - timedelta(days=impute_il_y_a)}
            # L'enregistrement précède l'imputation (~5 h) → temps moyens réalistes.
            Courrier.objects.filter(pk=c.pk).update(cree_le=upd['date_imputation'] - timedelta(hours=5))
            if accuse_by is not None:
                accuser_imputation(imp, accuse_by)
                upd['accuse_le'] = timezone.now() - timedelta(days=max(0, impute_il_y_a - 1))
            if relance_hier:
                upd['derniere_relance_le'] = timezone.now() - timedelta(days=1)
            Imputation.objects.filter(pk=imp.pk).update(**upd)
            if relance_hier:
                journaliser(c, 'RELANCE', secsg, {'direction': direction.sigle, 'commentaire': 'Relance (démo)'})
            if traiter_by is not None:
                imp.refresh_from_db()
                traiter_imputation(imp, traiter_by, f'Réponse transmise le {date.today():%d/%m/%Y}')
            return imp

        # --- Retards : 3 imputations (15, 7, 2 j) sur 2 directions (DGB, DGI) ---
        scenario(dgb, delai=j(-15), impute_il_y_a=18)                              # 15 j de retard (non accusé)
        scenario(dgi, delai=j(-7), impute_il_y_a=10, relance_hier=True)            # 7 j de retard, relancé hier
        scenario(dgb, delai=j(-2), accuse_by=secdgb, impute_il_y_a=6)             # 2 j de retard (accusé)
        # --- Confidentiel en retard (objet masqué pour la vue centrale) ---
        scenario(dgi, delai=j(-4), impute_il_y_a=5, confidentiel=True)
        # --- Délais proches (≤ 3 j) : 2 imputations ---
        scenario(dgd, delai=j(1), impute_il_y_a=3)                                 # échéance demain
        scenario(dgtcp, delai=j(2), impute_il_y_a=4)                              # échéance dans 2 j
        # --- Volume pour un tableau par direction parlant (ages variés) ---
        scenario(dgep, impute_il_y_a=12)
        scenario(dgep, impute_il_y_a=4)
        scenario(dgd, impute_il_y_a=8)
        scenario(dgtcp, impute_il_y_a=5)
        scenario(dgi, impute_il_y_a=9)
        scenario(dgb, accuse_by=secdgb, impute_il_y_a=7)
        # --- Cascade DGB → DBE → Division des dépenses (agrège dans la ligne DGB) ---
        i_root = scenario(dgb, instruction='POUR_ATTRIBUTION', accuse_by=secdgb, impute_il_y_a=11)
        i_dbe = creer_imputation(i_root.courrier, direction_cible=dbe, instruction='POUR_ATTRIBUTION',
                                 delai=None, commentaire='', impute_par=secdgb, imputation_mere=i_root)
        accuser_imputation(i_dbe, secdbe)
        creer_imputation(i_root.courrier, direction_cible=divdep, instruction='POUR_TRAITEMENT',
                         delai=None, commentaire='Traitement division', impute_par=secdbe, imputation_mere=i_dbe)
        # --- 1 imputation traitée (métrique accusé → traité) ---
        scenario(dgb, accuse_by=secdgb, impute_il_y_a=9, traiter_by=secdgb)

        # 6) Courrier DÉPART (lot C4) — 6 départs sur 2 structures émettrices
        dep_reg = Registre.objects.get(code='DEP')
        CompteurRegistre.objects.filter(registre=dep_reg, annee=date.today().year).update(dernier_numero=0)
        dgtcp = Direction.objects.get(sigle='DGTCP')
        corrs = list(Correspondant.objects.all()[:6])

        def scan_depart():
            return ContentFile(pdf_demo('Courrier depart signe'), name='depart.pdf')

        def depart(structure, objet, dest, *, scan=True, expedie_il_y_a=None, decharge_il_y_a=None,
                   ampliations=None, origine=None):
            d = creer_depart(
                enregistre_par=bo, structure_emettrice=structure, objet=objet, correspondant=dest,
                signataire_nom='M. le Secrétaire Général', signataire_qualite='Secrétaire Général',
                date_signature=date.today() - timedelta(days=2), ampliations=ampliations or [],
                courrier_origine=origine, scan=scan_depart() if scan else None)
            if expedie_il_y_a is not None:
                expedier_courrier(d, bo)
                Courrier.objects.filter(pk=d.pk).update(expedie_le=date.today() - timedelta(days=expedie_il_y_a))
                if decharge_il_y_a is not None:
                    d.refresh_from_db()
                    decharger_courrier(d, bo, date.today() - timedelta(days=decharge_il_y_a), 'Décharge signée (démo).')
            return d

        # une arrivée ordinaire encore en cours, à clôturer par le 1er départ
        arr_a_clore = (Courrier.objects
                       .filter(sens='ARRIVEE', statut__in=['IMPUTE', 'EN_TRAITEMENT'], confidentialite='ORDINAIRE')
                       .order_by('id').first())

        depart(dgb, "Réponse à la demande d'informations budgétaires", corrs[0],
               expedie_il_y_a=12, decharge_il_y_a=8, origine=arr_a_clore)          # déchargé + lié (clôture)
        depart(dgtcp, "Transmission de la situation mensuelle du Trésor", corrs[1],
               expedie_il_y_a=15, decharge_il_y_a=5)                               # déchargé (non lié)
        depart(dgb, "Notification d'ouverture de crédits budgétaires", corrs[2], expedie_il_y_a=3)   # expédié, 3 j
        depart(dgtcp, "Accusé de virement au partenaire technique", corrs[3], expedie_il_y_a=10)      # expédié, 10 j
        depart(dgb, "Projet de réponse (à scanner puis expédier)", corrs[4], scan=False)              # sans scan
        depart(dgtcp, "Circulaire relative à l'exécution budgétaire", corrs[0],
               ampliations=[corrs[1], corrs[2]], expedie_il_y_a=1)                 # 2 ampliations

        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(COURRIERS)} arrivées + scenario C3 + 6 départs C4 + {len(DEMO_USERS)} users demo.'))
