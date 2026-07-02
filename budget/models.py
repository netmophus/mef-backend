from django.db import models


class DocumentBudget(models.Model):
    """Document budgétaire (rubrique Budget), classé par rubrique et par année.

    Une même rubrique (ex. « lois-de-finances ») regroupe plusieurs documents
    répartis par année ; chaque document pointe vers un PDF téléversé ou un lien.
    Le `slug` de rubrique correspond au segment d'URL du frontend.
    """

    RUBRIQUE_CHOICES = [
        ('lois-de-finances', 'Lois de finances'),
        ('lois-de-reglement', 'Lois de règlement'),
        ('rapports-execution', "Rapports d'exécution"),
        ('reformes-budgetaires', 'Réformes budgétaires'),
        ('rapports-performance', 'Rapports de performance'),
        ('dppd', 'Programmation pluriannuelle (DPPD)'),
    ]

    rubrique = models.CharField('Rubrique', max_length=40, choices=RUBRIQUE_CHOICES,
                                db_index=True)
    annee = models.PositiveIntegerField('Année', db_index=True)
    titre = models.CharField('Titre', max_length=255)
    type = models.CharField('Type', max_length=120, blank=True,
                            help_text="Ex. : « Loi de finances initiale », « Rectificative »…")
    date = models.DateField('Date', blank=True, null=True)
    fichier = models.FileField('Fichier PDF', upload_to='budget/', blank=True, null=True)
    lien = models.CharField('Lien externe', max_length=300, blank=True,
                            help_text="Utilisé si aucun PDF n'est téléversé. « # » par défaut.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Document budgétaire'
        verbose_name_plural = 'Documents budgétaires'
        ordering = ['-annee', 'ordre', 'id']

    def __str__(self):
        return f'{self.get_rubrique_display()} {self.annee} — {self.titre}'
