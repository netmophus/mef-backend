from django.db import models


class Actualite(models.Model):
    """Article d'actualité du Ministère (Actualités › Dernières actualités).

    `image` = visuel officiel téléversé ; `image_url` = URL/chemin de secours
    (même principe que Slide / AlbumPhoto). `rubrique` sert au filtrage par
    onglets côté frontend ; `chapo` est le résumé affiché sur la carte.
    """

    RUBRIQUE_CHOICES = [
        ('Activités du Ministre', 'Activités du Ministre'),
        ('Événements', 'Événements'),
        ('Audiences & Rencontres', 'Audiences & Rencontres'),
        ('Communiqués', 'Communiqués'),
        ('Autre', 'Autre'),
    ]

    titre = models.CharField('Titre', max_length=255)
    rubrique = models.CharField('Rubrique', max_length=60, choices=RUBRIQUE_CHOICES,
                                default='Activités du Ministre')
    date = models.DateField('Date')
    chapo = models.TextField('Chapô (résumé)', blank=True,
                             help_text="Court résumé affiché sur la carte et en tête d'article.")
    contenu = models.TextField('Contenu', blank=True,
                               help_text='Corps de l\'article. Un paragraphe par ligne.')
    image = models.ImageField('Image', upload_to='actualites/', blank=True, null=True,
                              help_text="Visuel. Si vide, le champ « URL / chemin » est utilisé.")
    image_url = models.CharField('Image — URL ou chemin', max_length=500, blank=True,
                                 help_text="Utilisé si aucun fichier n'est téléversé.")
    a_la_une = models.BooleanField('À la une', default=False)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Actualité'
        verbose_name_plural = 'Actualités'
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.date} — {self.titre}'


class NumeroRevue(models.Model):
    """Numéro de la revue de presse (Actualités › Revue de presse), classé par année."""

    annee = models.PositiveIntegerField('Année', db_index=True)
    titre = models.CharField('Titre', max_length=255)
    date = models.DateField('Date', blank=True, null=True)
    fichier = models.FileField('Fichier PDF', upload_to='revue-presse/', blank=True, null=True)
    lien = models.CharField('Lien externe', max_length=300, blank=True,
                            help_text="Utilisé si aucun PDF n'est téléversé. « # » par défaut.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Numéro de revue de presse'
        verbose_name_plural = 'Revue de presse'
        ordering = ['-annee', 'ordre', 'id']

    def __str__(self):
        return f'{self.annee} — {self.titre}'
