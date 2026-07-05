"""Groupes RBAC régularisés (lot de clôture courrier).

Officialise en data migration deux groupes qui avaient été créés à la main en
base (constat de l'état des lieux) :

- LECTURE_SIMPLE     : consultation des courriers ordinaires uniquement
                       (permissions constatées en base réelle : consulter_courrier)
- ACCES_CONFIDENTIEL : accès aux courriers confidentiels (consulter_confidentiel)

Convention : tout groupe/permission passe par une data migration — jamais de
création manuelle en admin.
"""
from django.db import migrations

# codename → nom lisible (permissions du modèle courrier.Courrier)
PERMISSIONS = {
    'consulter_courrier': 'Peut consulter les courriers',
    'consulter_confidentiel': 'Peut consulter les courriers confidentiels',
}

GROUPES = {
    'LECTURE_SIMPLE': ['consulter_courrier'],
    'ACCES_CONFIDENTIEL': ['consulter_confidentiel'],
}


def seed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct, _ = ContentType.objects.get_or_create(app_label='courrier', model='courrier')
    perms = {}
    for codename, name in PERMISSIONS.items():
        perm, _ = Permission.objects.get_or_create(
            content_type=ct, codename=codename, defaults={'name': name})
        perms[codename] = perm

    for nom_groupe, codenames in GROUPES.items():
        groupe, _ = Group.objects.get_or_create(name=nom_groupe)
        groupe.permissions.set([perms[c] for c in codenames])


def unseed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUPES.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('courrier', '0007_courrier_date_signature_and_more'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [migrations.RunPython(seed, unseed)]
