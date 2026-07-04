"""Groupe RBAC du lot C3 (tableau de bord) : permission voir_tableau_bord.

- IMPUTATION_CENTRALE : tableau de bord du ministère entier
- SECRETARIAT        : tableau de bord restreint à son sous-arbre
"""
from django.db import migrations

PERMISSION = ('voir_tableau_bord', 'Peut consulter le tableau de bord de pilotage')
GROUPES = ['IMPUTATION_CENTRALE', 'SECRETARIAT']


def seed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct, _ = ContentType.objects.get_or_create(app_label='courrier', model='courrier')
    perm, _ = Permission.objects.get_or_create(
        content_type=ct, codename=PERMISSION[0], defaults={'name': PERMISSION[1]})

    for nom in GROUPES:
        groupe, _ = Group.objects.get_or_create(name=nom)
        groupe.permissions.add(perm)


def unseed(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    perm = Permission.objects.filter(codename=PERMISSION[0], content_type__app_label='courrier').first()
    if perm:
        for nom in GROUPES:
            g = Group.objects.filter(name=nom).first()
            if g:
                g.permissions.remove(perm)


class Migration(migrations.Migration):

    dependencies = [
        ('courrier', '0005_alter_courrier_options_and_more'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [migrations.RunPython(seed, unseed)]
