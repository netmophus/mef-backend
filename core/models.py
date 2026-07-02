from django.db import models


class SiteConfig(models.Model):
    """Réglages globaux du site : identité + coordonnées du Ministère.

    Table « singleton » : une seule ligne (toujours pk=1). Sert l'en-tête
    (titre, sous-titre, logo) et la barre utilitaire (téléphone, e-mail,
    réseaux sociaux).
    """

    # Identité
    nom = models.CharField('Nom du site', max_length=200, default='MINISTÈRE DES FINANCES')
    sous_titre = models.CharField('Sous-titre', max_length=200, default='République du Niger')
    logo = models.ImageField('Logo (armoiries)', upload_to='site/', blank=True, null=True)

    # Coordonnées
    telephone = models.CharField('Téléphone', max_length=50, blank=True)
    email = models.EmailField('E-mail', blank=True)
    adresse = models.CharField('Adresse', max_length=255, blank=True)

    # Réseaux sociaux
    facebook = models.URLField('Facebook', blank=True)
    twitter = models.URLField('X (Twitter)', blank=True)
    youtube = models.URLField('YouTube', blank=True)

    class Meta:
        verbose_name = 'Configuration du site'
        verbose_name_plural = 'Configuration du site'

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        # Force le singleton : on garde toujours la même ligne.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Renvoie l'unique configuration (la crée si absente)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MenuItem(models.Model):
    """Élément du menu de navigation principal.

    Auto-référencé : un item sans `parent` est de premier niveau ; un item
    avec `parent` est une entrée de sous-menu. Reproduit la structure de
    l'ancien `menuConfig.js`, mais éditable depuis l'admin.
    """

    label = models.CharField('Libellé', max_length=120)
    path = models.CharField('Lien (URL)', max_length=200, blank=True,
                            help_text="Laisser vide pour un menu qui ne sert qu'à regrouper des sous-entrées.")
    parent = models.ForeignKey(
        'self', verbose_name='Menu parent', related_name='enfants',
        on_delete=models.CASCADE, blank=True, null=True,
    )
    ordre = models.PositiveIntegerField('Ordre', default=0)
    visible = models.BooleanField('Visible', default=True)

    class Meta:
        verbose_name = 'Élément de menu'
        verbose_name_plural = 'Menu de navigation'
        ordering = ['ordre', 'id']

    def __str__(self):
        if self.parent:
            return f'{self.parent.label} › {self.label}'
        return self.label


class LienUtile(models.Model):
    """Lien utile (S'informer › Liens & Partenaires) — site institutionnel."""

    label = models.CharField('Libellé', max_length=200)
    url = models.CharField('Lien', max_length=300, default='#',
                           help_text="URL du site. « # » tant que l'adresse n'est pas connue.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Lien utile'
        verbose_name_plural = 'Liens utiles'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.label


class Partenaire(models.Model):
    """Partenaire technique et financier (S'informer › Liens & Partenaires)."""

    nom = models.CharField('Nom', max_length=120)
    sigle = models.CharField('Sigle / description', max_length=120, blank=True)
    initiales = models.CharField('Initiales', max_length=4, blank=True,
                                 help_text="Affichées dans la pastille si aucun logo. Ex. « FMI ».")
    logo = models.ImageField('Logo', upload_to='partenaires/', blank=True, null=True)
    url = models.CharField('Lien', max_length=300, default='#')
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.nom


class BlocReforme(models.Model):
    """Carte « Réforme des finances publiques » (bloc Liens & Partenaires).

    Table singleton (pk=1) : titre, texte et lien éditables depuis l'admin.
    """

    etiquette = models.CharField('Étiquette', max_length=60, default='Réforme')
    titre = models.CharField('Titre', max_length=200, default='Réforme des finances publiques')
    texte = models.TextField(
        'Texte',
        default="Modernisation de la gestion publique : transparence budgétaire, "
                "dématérialisation et conformité aux directives de l'UEMOA (programme PEFA).",
    )
    bouton_label = models.CharField('Bouton — libellé', max_length=80, default='En savoir plus')
    bouton_url = models.CharField('Bouton — lien', max_length=300,
                                  default='/budget/reformes-budgetaires')
    image = models.ImageField('Image', upload_to='reforme/', blank=True, null=True,
                              help_text="Visuel de fond. Si vide, le champ « URL / chemin » est utilisé.")
    image_url = models.CharField(
        'Image — URL ou chemin', max_length=500, blank=True,
        default='https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80',
    )

    class Meta:
        verbose_name = 'Bloc « Réforme »'
        verbose_name_plural = 'Bloc « Réforme »'

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
