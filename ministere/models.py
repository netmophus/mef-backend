from django.db import models


class Ministre(models.Model):
    """Le Ministre (identité affichée sur l'accueil). Table singleton (pk=1)."""

    nom = models.CharField('Nom (carte accueil)', max_length=200, default='Dr Maman Laouali ABDOU RAFA')
    fonction = models.CharField('Fonction', max_length=200,
                                default="Ministre de l'Économie et des Finances")
    photo = models.ImageField('Photo', upload_to='ministre/', blank=True, null=True)
    etiquette = models.CharField('Étiquette', max_length=60, default='Le Ministre',
                                 help_text="Petit libellé en haut de la photo.")

    # --- Page biographie ---
    nom_complet = models.CharField('Nom complet (biographie)', max_length=200, blank=True,
                                   help_text='Ex. : « Docteur Maman Laouali ABDOU RAFA ».')
    presentation_accroche = models.TextField('Présentation — accroche', blank=True,
                                             help_text='Phrase mise en avant en tête de présentation.')
    presentation_corps = models.TextField('Présentation — corps', blank=True)
    experience = models.TextField('Expérience & expertise', blank=True,
                                  help_text='Un paragraphe par ligne.')
    conseils_periode = models.CharField("Conseils — période", max_length=60, blank=True,
                                        help_text='Ex. : « 2016 – 2021 ».')
    conseils = models.TextField("Conseils d'administration", blank=True,
                                help_text='Un sigle par ligne (BCEAO, BOAD, …).')

    class Meta:
        verbose_name = 'Le Ministre'
        verbose_name_plural = 'Le Ministre'

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MinistreLien(models.Model):
    """Lien rapide affiché sous la photo du Ministre (accueil)."""

    ICONE_CHOICES = [
        ('menu_book', 'Livre (biographie)'),
        ('groups', 'Groupe (cabinet)'),
        ('record_voice_over', 'Discours / voix'),
        ('description', 'Document'),
        ('link', 'Lien générique'),
    ]

    label = models.CharField('Libellé', max_length=150)
    icone = models.CharField('Icône', max_length=40, choices=ICONE_CHOICES, default='link')
    href = models.CharField('Lien', max_length=300, default='#',
                            help_text="« # » tant que la page n'existe pas encore.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Lien du Ministre'
        verbose_name_plural = 'Liens du Ministre'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.label


class MinistreRepere(models.Model):
    """Repère biographique (icône + texte) : naissance, famille, langues…"""

    ICONE_CHOICES = [
        ('cake', 'Gâteau (naissance)'),
        ('family', 'Famille'),
        ('translate', 'Langues'),
        ('school', 'Formation'),
        ('work', 'Travail'),
        ('place', 'Lieu'),
    ]

    ministre = models.ForeignKey(Ministre, related_name='reperes', on_delete=models.CASCADE)
    icone = models.CharField('Icône', max_length=40, choices=ICONE_CHOICES, default='place')
    texte = models.CharField('Texte', max_length=255)
    ordre = models.PositiveIntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Repère biographique'
        verbose_name_plural = 'Repères biographiques'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.texte


class MinistreParcours(models.Model):
    """Étape de formation ou de parcours professionnel (frise chronologique)."""

    CATEGORIE_CHOICES = [
        ('formation', 'Formation'),
        ('professionnel', 'Parcours professionnel'),
    ]

    ministre = models.ForeignKey(Ministre, related_name='parcours', on_delete=models.CASCADE)
    categorie = models.CharField('Catégorie', max_length=20, choices=CATEGORIE_CHOICES)
    periode = models.CharField('Période', max_length=80)
    titre = models.CharField('Titre', max_length=255)
    detail = models.CharField('Détail / Organisme', max_length=255, blank=True)
    ordre = models.PositiveIntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Étape (formation / parcours)'
        verbose_name_plural = 'Étapes (formation / parcours)'
        ordering = ['ordre', 'id']

    def __str__(self):
        return f'{self.get_categorie_display()} — {self.titre}'


class MembreCabinet(models.Model):
    """Membre du cabinet du ministre (trombinoscope)."""

    nom = models.CharField('Nom', max_length=200)
    fonction = models.CharField('Fonction', max_length=200)
    photo = models.ImageField('Photo', upload_to='cabinet/', blank=True, null=True)
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Membre du cabinet'
        verbose_name_plural = 'Cabinet — membres'
        ordering = ['ordre', 'id']

    def __str__(self):
        return f'{self.nom} — {self.fonction}'


class Discours(models.Model):
    """Discours / communication du ministre."""

    titre = models.CharField('Titre', max_length=255)
    date = models.DateField('Date')
    extrait = models.TextField('Extrait', blank=True)
    fichier = models.FileField('Fichier PDF', upload_to='discours/', blank=True, null=True)
    lien = models.CharField('Lien externe', max_length=300, blank=True,
                            help_text="Utilisé si aucun PDF n'est fourni (ex. vidéo).")
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Discours'
        verbose_name_plural = 'Discours'
        ordering = ['-date', '-id']

    def __str__(self):
        return self.titre


class AlbumPhoto(models.Model):
    """Photo de l'album du Ministre (Le Ministère › Album photo du Ministre).

    `image` = visuel officiel téléversé (servi depuis /media/).
    `image_url` = URL externe ou chemin frontend (ex. /DrRafa.jpeg) utilisé
    tant qu'aucun fichier n'est téléversé. Même principe que Slide.
    Les photos sont regroupées par `categorie` (onglets côté frontend).
    """

    CATEGORIE_CHOICES = [
        ('Portraits', 'Portraits'),
        ('Activités', 'Activités'),
        ('Audiences', 'Audiences'),
        ('Cérémonies', 'Cérémonies'),
    ]

    titre = models.CharField('Titre / légende', max_length=255)
    categorie = models.CharField('Catégorie (onglet)', max_length=40,
                                 choices=CATEGORIE_CHOICES, default='Activités')
    image = models.ImageField('Photo', upload_to='album-ministre/', blank=True, null=True,
                              help_text="Visuel officiel. Si vide, le champ « URL / chemin » est utilisé.")
    image_url = models.CharField('Image — URL ou chemin', max_length=500, blank=True,
                                 help_text="Utilisé si aucun fichier n'est téléversé. Ex. https://… ou /DrRafa.jpeg")
    date = models.DateField('Date', blank=True, null=True,
                            help_text='Mois affiché sous la photo (le jour est ignoré).')
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = "Photo de l'album"
        verbose_name_plural = "Album photo du Ministre"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f'{self.categorie} — {self.titre}'


class Evenement(models.Model):
    """Événement de l'agenda du Ministère (Le Ministère › Événements)."""

    TYPE_CHOICES = [
        ('Conférence', 'Conférence'),
        ('Atelier', 'Atelier'),
        ('Réunion', 'Réunion'),
        ('Cérémonie', 'Cérémonie'),
        ('Mission', 'Mission'),
        ('Autre', 'Autre'),
    ]

    titre = models.CharField('Titre', max_length=255)
    type = models.CharField('Type', max_length=40, choices=TYPE_CHOICES, default='Autre')
    date_debut = models.DateField('Date (début)')
    date_fin = models.DateField('Date (fin)', blank=True, null=True,
                                help_text="À renseigner seulement si l'événement dure plusieurs jours.")
    heure = models.CharField('Heure', max_length=40, blank=True,
                             help_text='Ex. : « 09h00 » ou « 09h00 – 13h00 ».')
    lieu = models.CharField('Lieu', max_length=200, blank=True)
    description = models.TextField('Description', blank=True)
    image = models.ImageField('Image', upload_to='evenements/', blank=True, null=True,
                              help_text="Visuel. Si vide, le champ « URL / chemin » est utilisé.")
    image_url = models.CharField('Image — URL ou chemin', max_length=500, blank=True,
                                 help_text="Utilisé si aucun fichier n'est téléversé.")
    lien = models.CharField('Lien (détails / inscription)', max_length=300, blank=True)
    a_la_une = models.BooleanField('À la une', default=False)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'
        ordering = ['-date_debut', '-id']

    def __str__(self):
        return f'{self.date_debut} — {self.titre}'


class Denomination(models.Model):
    """Dénomination successive du Ministère (Historique — frise chronologique)."""

    an = models.CharField('Année', max_length=40, help_text="Ex. : « 1958 » ou « Depuis 2023 ».")
    nom = models.CharField('Dénomination', max_length=255)
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Dénomination (historique)'
        verbose_name_plural = 'Historique — dénominations'
        ordering = ['ordre', 'id']

    def __str__(self):
        return f'{self.an} — {self.nom}'


class MinistreHistorique(models.Model):
    """Ministre / délégué figurant dans les galeries de l'Historique.

    `photo` = fichier téléversé ; `photo_url` = chemin officiel (ex. /DrRafa.jpeg) ;
    `secours` = image de secours (URL). `categorie` sépare les deux galeries.
    """

    CATEGORIE_CHOICES = [
        ('ministre', 'Ministre des Finances'),
        ('delegue', "Ministre délégué / Secrétaire d'État"),
    ]

    categorie = models.CharField('Catégorie', max_length=20, choices=CATEGORIE_CHOICES,
                                 default='ministre', db_index=True)
    nom = models.CharField('Nom', max_length=200)
    description = models.CharField('Description', max_length=255, blank=True)
    photo = models.ImageField('Photo', upload_to='ministres/', blank=True, null=True)
    photo_url = models.CharField('Photo — URL ou chemin', max_length=500, blank=True,
                                 help_text="Utilisé si aucun fichier n'est téléversé.")
    secours = models.URLField('Image de secours (URL)', blank=True)
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Ministre (historique)'
        verbose_name_plural = 'Historique — ministres & délégués'
        ordering = ['categorie', 'ordre', 'id']

    def __str__(self):
        return f'{self.get_categorie_display()} — {self.nom}'


class TexteOrganisation(models.Model):
    """Décret portant organisation du Ministère (Historique › Textes portant organisation)."""

    titre = models.TextField('Titre')
    annee = models.CharField('Année', max_length=10, blank=True)
    fichier = models.FileField('Fichier PDF', upload_to='textes/', blank=True, null=True)
    lien = models.CharField('Lien externe', max_length=400, blank=True,
                            help_text="Utilisé si aucun PDF n'est téléversé. « # » par défaut.")
    ordre = models.PositiveIntegerField('Ordre', default=0)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = "Texte portant organisation"
        verbose_name_plural = 'Historique — textes portant organisation'
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.titre[:80]
