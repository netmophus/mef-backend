from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Direction(models.Model):
    """Direction / structure du Ministère (arborescence via `parent`)."""

    sigle = models.CharField('Sigle', max_length=20, unique=True)
    nom = models.CharField('Nom', max_length=255)
    parent = models.ForeignKey(
        'self', verbose_name='Rattachée à', null=True, blank=True,
        on_delete=models.PROTECT, related_name='sous_directions',
    )
    ordre = models.PositiveSmallIntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Direction'
        verbose_name_plural = 'Directions'
        ordering = ['ordre', 'sigle']

    def __str__(self):
        return f'{self.sigle} — {self.nom}'

    def get_descendants(self, inclure_soi=True):
        """Direction + toutes ses sous-directions (récursif). Cache par instance."""
        descendants = getattr(self, '_descendants_cache', None)
        if descendants is None:
            descendants = []
            for enfant in self.sous_directions.all():
                descendants.extend(enfant.get_descendants(inclure_soi=True))
            self._descendants_cache = descendants
        return ([self] if inclure_soi else []) + list(descendants)

    def descendant_ids(self, inclure_soi=True):
        return [d.id for d in self.get_descendants(inclure_soi=inclure_soi)]


class UtilisateurManager(BaseUserManager):
    """Manager du modèle Utilisateur (identifiant = matricule, pas d'username)."""

    use_in_migrations = True

    def create_user(self, matricule, password=None, **extra_fields):
        if not matricule:
            raise ValueError('Le matricule est obligatoire.')
        user = self.model(matricule=matricule, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matricule, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # Un superuser (créé en ligne de commande) n'est pas forcé de changer son mdp.
        extra_fields.setdefault('doit_changer_mdp', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Un superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Un superuser doit avoir is_superuser=True.')
        return self.create_user(matricule, password, **extra_fields)


class Utilisateur(AbstractUser):
    """Utilisateur de l'intranet. Connexion par matricule (pas d'username)."""

    username = None
    matricule = models.CharField('Matricule', max_length=30, unique=True)

    direction = models.ForeignKey(
        Direction, verbose_name='Direction', null=True, blank=True,
        on_delete=models.PROTECT, related_name='agents',
    )
    fonction = models.CharField('Fonction', max_length=150, blank=True)
    superieur = models.ForeignKey(
        'self', verbose_name='Supérieur hiérarchique', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='subordonnes',
    )
    telephone = models.CharField('Téléphone', max_length=30, blank=True)
    bureau = models.CharField('Bureau', max_length=100, blank=True)
    doit_changer_mdp = models.BooleanField(
        'Doit changer son mot de passe', default=True,
        help_text='Force le changement de mot de passe à la prochaine connexion.',
    )

    USERNAME_FIELD = 'matricule'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UtilisateurManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['matricule']

    def __str__(self):
        nom = self.get_full_name()
        return f'{self.matricule} — {nom}' if nom else self.matricule
