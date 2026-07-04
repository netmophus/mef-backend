"""Seed des référentiels courrier + permissions custom + groupes RBAC.

Data migration (les permissions sont créées ici par get_or_create pour ne pas
dépendre du timing du hook post_migrate).
"""
from django.db import migrations

PERMISSIONS = [
    ('enregistrer_courrier', 'Peut enregistrer un courrier'),
    ('modifier_courrier', 'Peut modifier un courrier'),
    ('consulter_courrier', 'Peut consulter les courriers'),
    ('consulter_confidentiel', 'Peut consulter les courriers confidentiels'),
    ('classer_courrier', 'Peut classer un courrier sans suite'),
]

REGISTRES = [
    ('ARR', 'Courrier arrivée', 'ARRIVEE'),
    ('DEP', 'Courrier départ', 'DEPART'),
]

CORRESPONDANTS = [
    ('BCEAO', 'BANQUE'),
    ('FMI', 'PARTENAIRE_INTERNATIONAL'),
    ('Banque Mondiale', 'PARTENAIRE_INTERNATIONAL'),
    ('Primature', 'INSTITUTION_PUBLIQUE'),
    ('Présidence de la République', 'INSTITUTION_PUBLIQUE'),
    ('BSIC Niger', 'BANQUE'),
    ('SONIBANK', 'BANQUE'),
    ('DGI (interne)', 'INSTITUTION_PUBLIQUE'),
    ('Trésor National', 'INSTITUTION_PUBLIQUE'),
    ('Divers', 'AUTRE'),
]

GROUPES = {
    'BUREAU_ORDRE': [c for c, _ in PERMISSIONS],
    'LECTURE_COURRIER_CENTRALE': ['consulter_courrier', 'consulter_confidentiel'],
}


def seed(apps, schema_editor):
    Registre = apps.get_model('courrier', 'Registre')
    Correspondant = apps.get_model('courrier', 'Correspondant')
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Référentiels
    for code, libelle, sens in REGISTRES:
        Registre.objects.get_or_create(code=code, defaults={'libelle': libelle, 'sens': sens})
    for nom, type_ in CORRESPONDANTS:
        Correspondant.objects.get_or_create(nom=nom, defaults={'type': type_})

    # Permissions custom (idempotent, indépendant du hook post_migrate)
    ct, _ = ContentType.objects.get_or_create(app_label='courrier', model='courrier')
    perms = {}
    for codename, name in PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(
            content_type=ct, codename=codename, defaults={'name': name})
        perms[codename] = perm

    # Groupes
    for nom_groupe, codenames in GROUPES.items():
        groupe, _ = Group.objects.get_or_create(name=nom_groupe)
        groupe.permissions.set([perms[c] for c in codenames])


def unseed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUPES.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('courrier', '0001_initial'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
