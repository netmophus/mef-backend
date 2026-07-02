from django.db import models


class Photo(models.Model):
    """Photo de la galerie (Médiathèque › Photos).

    `image` = fichier téléversé ; `image_url` = URL/chemin de secours.
    """

    titre = models.CharField('Titre', max_length=255)
    image = models.ImageField('Image', upload_to='galerie/', blank=True, null=True,
                              help_text="Visuel. Si vide, le champ « URL / chemin » est utilisé.")
    image_url = models.CharField('Image — URL ou chemin', max_length=500, blank=True)
    date = models.DateField('Date', blank=True, null=True)
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Photo'
        verbose_name_plural = 'Photos (galerie)'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.titre


class Video(models.Model):
    """Vidéo (Médiathèque › Vidéos).

    `miniature` = image téléversée ; `miniature_url` = URL/chemin de secours.
    `lien` = URL de la vidéo (YouTube, MP4…).
    """

    titre = models.CharField('Titre', max_length=255)
    date = models.DateField('Date', blank=True, null=True)
    duree = models.CharField('Durée', max_length=12, blank=True, help_text='Ex. : « 4:35 ».')
    miniature = models.ImageField('Miniature', upload_to='videos/', blank=True, null=True)
    miniature_url = models.CharField('Miniature — URL ou chemin', max_length=500, blank=True)
    lien = models.CharField('Lien de la vidéo', max_length=400, blank=True,
                            help_text='URL YouTube / MP4. « # » par défaut.')
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Vidéo'
        verbose_name_plural = 'Vidéos'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.titre
