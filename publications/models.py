from django.db import models


class Publication(models.Model):
    """Publication du Ministère, classée par rubrique (sous-page Publications).

    Le `slug` de rubrique correspond au segment d'URL du frontend. `type` sert
    d'étiquette et de filtre (ex. « Bulletin », « Arrêté », ou une année comme
    « 2020 » pour les états financiers).
    """

    RUBRIQUE_CHOICES = [
        ('ministere', 'Publications du Ministère'),
        ('autres', 'Autres publications'),
        ('etats-financiers', 'États Financiers'),
    ]

    rubrique = models.CharField('Rubrique', max_length=30, choices=RUBRIQUE_CHOICES, db_index=True)
    type = models.CharField('Type / étiquette', max_length=60,
                            help_text="Ex. : « Bulletin », « Arrêté », « 2020 »…")
    titre = models.TextField('Titre')
    fichier = models.FileField('Fichier PDF', upload_to='publications/', blank=True, null=True)
    lien = models.CharField('Lien externe', max_length=400, blank=True,
                            help_text="Utilisé si aucun PDF n'est téléversé. « # » par défaut.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'
        ordering = ['rubrique', 'ordre', 'id']

    def __str__(self):
        return f'{self.get_rubrique_display()} — {self.type}'
