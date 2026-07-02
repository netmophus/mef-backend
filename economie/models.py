from django.db import models


class IndicateurMacro(models.Model):
    """Grand indicateur (carte colorée animée) — ex. PIB Nominal, Inflation."""

    ICONE_CHOICES = [
        ('paid', 'Monnaie (PIB)'),
        ('trending_up', 'Croissance'),
        ('show_chart', 'Courbe (inflation)'),
        ('request_quote', 'Financement'),
        ('account_balance', 'Institution'),
        ('savings', 'Épargne'),
    ]

    label = models.CharField('Libellé', max_length=120)
    valeur = models.FloatField('Valeur')
    decimales = models.PositiveSmallIntegerField('Décimales', default=0,
                                                 help_text="Nombre de décimales à l'affichage.")
    suffixe = models.CharField('Suffixe', max_length=10, blank=True, help_text="Ex. : « % ».")
    unite = models.CharField('Unité / précision', max_length=60, blank=True,
                             help_text="Ex. : « Milliards FCFA » ou « Mars 2026 ».")
    icone = models.CharField('Icône', max_length=30, choices=ICONE_CHOICES, default='paid')
    couleur_debut = models.CharField('Couleur (début)', max_length=7, default='#0a5ca8')
    couleur_fin = models.CharField('Couleur (fin)', max_length=7, default='#002B55')
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Grand indicateur'
        verbose_name_plural = 'Indicateurs — grands (cartes)'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.label


class IndicateurCle(models.Model):
    """Indicateur clé affiché en jauge circulaire — ex. Taux de croissance."""

    label = models.CharField('Libellé', max_length=120)
    valeur = models.FloatField('Valeur (%)')
    maximum = models.FloatField('Maximum de la jauge', default=100)
    couleur = models.CharField('Couleur', max_length=7, default='#2E8B57')
    note = models.CharField('Note', max_length=80, blank=True,
                            help_text="Ex. : « en % du PIB · 2025 ».")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Indicateur clé (jauge)'
        verbose_name_plural = 'Indicateurs — clés (jauges)'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.label
