from django.db import models


class Slide(models.Model):
    """Diapositive du carrousel d'accueil (HeroSlider).

    `image` = visuel officiel uploadé (servi depuis /media/).
    `secours` = image de secours (URL) affichée tant que `image` est absente.
    """

    ICONE_CHOICES = [
        ('arrow', 'Flèche'),
        ('download', 'Téléchargement'),
    ]

    categorie = models.CharField('Catégorie', max_length=120)
    titre = models.CharField('Titre', max_length=200)
    texte = models.TextField('Texte')

    image = models.ImageField(
        'Image officielle', upload_to='slides/', blank=True, null=True,
        help_text="Visuel officiel. Si vide, l'image de secours est utilisée.",
    )
    secours = models.URLField(
        'Image de secours (URL)', blank=True,
        help_text="Affichée tant que l'image officielle est absente.",
    )
    position = models.CharField(
        'Cadrage', max_length=50, blank=True,
        help_text="Optionnel. Ex. : « center » ou « center top ».",
    )

    # Bouton principal (obligatoire)
    cta_label = models.CharField('Bouton — libellé', max_length=120)
    cta_href = models.CharField('Bouton — lien', max_length=200)
    cta_icon = models.CharField('Bouton — icône', max_length=10, choices=ICONE_CHOICES, default='arrow')

    # Bouton secondaire (optionnel)
    cta2_label = models.CharField('Bouton 2 — libellé', max_length=120, blank=True)
    cta2_href = models.CharField('Bouton 2 — lien', max_length=200, blank=True)

    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Slide (carrousel)'
        verbose_name_plural = 'Slides (carrousel)'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.titre


class QuickLink(models.Model):
    """Bouton « Accès rapides » de l'accueil (lien vers un service/outil).

    L'icône est stockée sous forme de clé ; le frontend la convertit en
    icône Material UI.
    """

    ICONE_CHOICES = [
        ('computer', 'Ordinateur'),
        ('gavel', 'Marteau (justice / marchés)'),
        ('account_balance', 'Institution / banque'),
        ('receipt_long', 'Reçu / impôts'),
        ('description', 'Document'),
        ('payments', 'Paiements'),
        ('public', 'Globe / public'),
        ('link', 'Lien générique'),
    ]

    nom = models.CharField('Nom', max_length=120)
    icone = models.CharField('Icône', max_length=40, choices=ICONE_CHOICES, default='link')
    couleur_debut = models.CharField('Couleur (début)', max_length=7, default='#0a5ca8',
                                     help_text='Code hexadécimal, ex. #0a5ca8')
    couleur_fin = models.CharField('Couleur (fin)', max_length=7, default='#002B55',
                                   help_text='Code hexadécimal, ex. #002B55')
    href = models.CharField('Lien', max_length=300, default='#',
                            help_text="URL du service. « # » tant que l'adresse n'est pas connue.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Accès rapide'
        verbose_name_plural = 'Accès rapides'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.nom
