"""Groupes RBAC du lot C2 (imputations).

- IMPUTATION_CENTRALE : imputer au 1er niveau + consulter (courriers non confidentiels)
- SECRETARIAT        : accuser réception, sous-imputer, marquer traité
"""
from django.db import migrations

PERMISSIONS = [
    ('imputer_premier_niveau', 'Peut imputer un courrier au premier niveau'),
    ('imputer_sous_arbre', 'Peut sous-imputer dans son sous-arbre'),
    ('accuser_reception', "Peut accuser réception d'une imputation"),
    ('marquer_traite', 'Peut marquer une imputation traitée'),
    ('consulter_courrier', 'Peut consulter les courriers'),
]

GROUPES = {
    'IMPUTATION_CENTRALE': ['consulter_courrier', 'imputer_premier_niveau'],
    'SECRETARIAT': ['accuser_reception', 'imputer_sous_arbre', 'marquer_traite'],
}


def seed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct, _ = ContentType.objects.get_or_create(app_label='courrier', model='courrier')
    perms = {}
    for codename, name in PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(content_type=ct, codename=codename, defaults={'name': name})
        perms[codename] = perm

    for nom_groupe, codenames in GROUPES.items():
        groupe, _ = Group.objects.get_or_create(name=nom_groupe)
        groupe.permissions.set([perms[c] for c in codenames])


def unseed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUPES.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('courrier', '0003_alter_courrier_options_alter_evenementcourrier_type_and_more'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [migrations.RunPython(seed, unseed)]
