from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone


class Registre(models.Model):
    """Registre de courrier (ex. ARR = arrivée, DEP = départ)."""

    SENS = [('ARRIVEE', 'Arrivée'), ('DEPART', 'Départ')]

    code = models.CharField('Code', max_length=10, unique=True)
    libelle = models.CharField('Libellé', max_length=100)
    sens = models.CharField('Sens', max_length=10, choices=SENS)
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Registre'
        verbose_name_plural = 'Registres'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.libelle}'


class CompteurRegistre(models.Model):
    """Compteur d'ordre par registre et par année (numérotation à verrou)."""

    registre = models.ForeignKey(Registre, on_delete=models.PROTECT, related_name='compteurs')
    annee = models.PositiveIntegerField('Année')
    dernier_numero = models.PositiveIntegerField('Dernier numéro', default=0)

    class Meta:
        verbose_name = 'Compteur de registre'
        verbose_name_plural = 'Compteurs de registre'
        unique_together = [('registre', 'annee')]
        ordering = ['registre', '-annee']

    def __str__(self):
        return f'{self.registre.code} {self.annee} : {self.dernier_numero}'


class Correspondant(models.Model):
    """Émetteur (arrivée) ou destinataire (départ) d'un courrier."""

    TYPES = [
        ('INSTITUTION_PUBLIQUE', 'Institution publique'),
        ('PARTENAIRE_INTERNATIONAL', 'Partenaire international'),
        ('BANQUE', 'Banque'),
        ('ENTREPRISE', 'Entreprise'),
        ('PARTICULIER', 'Particulier'),
        ('AUTRE', 'Autre'),
    ]

    nom = models.CharField('Nom', max_length=255, unique=True)
    type = models.CharField('Type', max_length=30, choices=TYPES, default='AUTRE')
    actif = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Correspondant'
        verbose_name_plural = 'Correspondants'
        ordering = ['nom']

    def __str__(self):
        return self.nom


def chemin_scan(instance, filename):
    """courriers/AAAA/MM/{numero_ordre}.pdf (le numéro est fixé avant l'upload)."""
    d = timezone.localdate()
    return f'courriers/{d.year}/{d.month:02d}/{instance.numero_ordre}.pdf'


class Courrier(models.Model):
    """Courrier enregistré au Bureau d'Ordre."""

    SENS = [('ARRIVEE', 'Arrivée'), ('DEPART', 'Départ')]
    CONFIDENTIALITE = [('ORDINAIRE', 'Ordinaire'), ('CONFIDENTIEL', 'Confidentiel')]
    STATUT = [
        ('ENREGISTRE', 'Enregistré'),
        ('IMPUTE', 'Imputé'),
        ('EN_TRAITEMENT', 'En traitement'),
        ('TRAITE', 'Traité'),
        ('CLASSE', 'Classé sans suite'),
    ]

    registre = models.ForeignKey(Registre, on_delete=models.PROTECT, related_name='courriers')
    numero_ordre = models.CharField("Numéro d'ordre", max_length=30, unique=True, editable=False)
    sens = models.CharField('Sens', max_length=10, choices=SENS, default='ARRIVEE')

    date_document = models.DateField('Date du document')
    date_arrivee = models.DateField("Date d'arrivée", default=date.today)

    correspondant = models.ForeignKey(Correspondant, on_delete=models.PROTECT, related_name='courriers')
    objet = models.CharField('Objet', max_length=500)
    confidentialite = models.CharField('Confidentialité', max_length=15,
                                       choices=CONFIDENTIALITE, default='ORDINAIRE')
    nombre_pieces = models.PositiveSmallIntegerField('Nombre de pièces', default=1)
    delai_reponse = models.DateField('Délai de réponse', null=True, blank=True)
    statut = models.CharField('Statut', max_length=15, choices=STATUT, default='ENREGISTRE')

    scan = models.FileField('Scan (PDF)', upload_to=chemin_scan, null=True, blank=True)
    hash_sha256 = models.CharField('Empreinte SHA-256', max_length=64, editable=False, blank=True)

    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                       related_name='courriers_enregistres')
    # Prêt pour le lot C4 (réponse à un courrier) — inutilisé ici.
    courrier_origine = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name='reponses')

    cree_le = models.DateTimeField('Créé le', auto_now_add=True)
    modifie_le = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Courrier'
        verbose_name_plural = 'Courriers'
        ordering = ['-date_arrivee', '-numero_ordre']
        permissions = [
            ('enregistrer_courrier', 'Peut enregistrer un courrier'),
            ('modifier_courrier', 'Peut modifier un courrier'),
            ('consulter_courrier', 'Peut consulter les courriers'),
            ('consulter_confidentiel', 'Peut consulter les courriers confidentiels'),
            ('classer_courrier', 'Peut classer un courrier sans suite'),
            ('imputer_premier_niveau', 'Peut imputer un courrier au premier niveau'),
            ('imputer_sous_arbre', 'Peut sous-imputer dans son sous-arbre'),
            ('accuser_reception', "Peut accuser réception d'une imputation"),
            ('marquer_traite', 'Peut marquer une imputation traitée'),
            ('voir_tableau_bord', 'Peut consulter le tableau de bord de pilotage'),
        ]

    def __str__(self):
        return f'{self.numero_ordre} — {self.objet[:60]}'


class EvenementCourrier(models.Model):
    """Journal des transitions/actions sur un courrier (jamais un simple update)."""

    TYPES = [
        ('ENREGISTREMENT', 'Enregistrement'),
        ('MODIFICATION', 'Modification'),
        ('REMPLACEMENT_SCAN', 'Remplacement du scan'),
        ('CLASSEMENT', 'Classement sans suite'),
        ('IMPUTATION', 'Imputation'),
        ('SOUS_IMPUTATION', 'Sous-imputation'),
        ('ACCUSE_RECEPTION', 'Accusé de réception'),
        ('MARQUE_TRAITE', 'Marqué traité'),
        ('RETOUR_IMPUTATION', "Annulation d'imputation"),
        ('RELANCE', 'Relance'),
    ]

    courrier = models.ForeignKey(Courrier, on_delete=models.CASCADE, related_name='evenements')
    type = models.CharField('Type', max_length=20, choices=TYPES)
    acteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                               related_name='evenements_courrier')
    horodatage = models.DateTimeField('Horodatage', auto_now_add=True)
    details = models.JSONField('Détails', default=dict, blank=True)

    class Meta:
        verbose_name = 'Événement de courrier'
        verbose_name_plural = 'Événements de courrier'
        ordering = ['-horodatage']

    def __str__(self):
        return f'{self.get_type_display()} — {self.courrier.numero_ordre}'


class Imputation(models.Model):
    """Imputation d'un courrier vers une direction (avec cascade via imputation_mere)."""

    INSTRUCTION = [
        ('POUR_TRAITEMENT', 'Pour traitement'),
        ('POUR_AVIS', 'Pour avis'),
        ('POUR_INFORMATION', 'Pour information'),
        ('POUR_ATTRIBUTION', 'Pour attribution'),
        ('M_EN_PARLER', "M'en parler"),
    ]
    STATUT = [
        ('EN_ATTENTE_ACCUSE', "En attente d'accusé"),
        ('ACCUSEE', 'Accusée'),
        ('TRAITEE', 'Traitée'),
    ]

    courrier = models.ForeignKey(Courrier, on_delete=models.CASCADE, related_name='imputations')
    imputation_mere = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,
                                        related_name='sous_imputations')
    direction_cible = models.ForeignKey('comptes.Direction', on_delete=models.PROTECT,
                                        related_name='imputations')
    instruction = models.CharField('Instruction', max_length=20, choices=INSTRUCTION)
    delai = models.DateField('Délai', null=True, blank=True)
    commentaire = models.CharField('Commentaire', max_length=500, blank=True)

    impute_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name='imputations_faites')
    date_imputation = models.DateTimeField('Date', auto_now_add=True)

    accuse_le = models.DateTimeField('Accusé le', null=True, blank=True)
    accuse_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.PROTECT, related_name='imputations_accusees')

    traite_le = models.DateTimeField('Traité le', null=True, blank=True)
    traite_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.PROTECT, related_name='imputations_traitees')
    commentaire_traitement = models.CharField('Commentaire de traitement', max_length=500, blank=True)

    statut = models.CharField('Statut', max_length=20, choices=STATUT, default='EN_ATTENTE_ACCUSE')

    # Dénormalisation (lot C3) : dernière relance manuelle, pour la mise en
    # évidence rapide dans les bannettes et le tableau de bord.
    derniere_relance_le = models.DateTimeField('Dernière relance le', null=True, blank=True)

    # Soft delete (annulation / retour d'imputation)
    annulee_le = models.DateTimeField('Annulée le', null=True, blank=True)
    annulee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.PROTECT, related_name='imputations_annulees')

    class Meta:
        verbose_name = 'Imputation'
        verbose_name_plural = 'Imputations'
        ordering = ['date_imputation', 'id']

    def __str__(self):
        return f'{self.courrier.numero_ordre} → {self.direction_cible.sigle} ({self.get_instruction_display()})'

    @property
    def active(self):
        return self.annulee_le is None

    @property
    def est_premier_niveau(self):
        return self.imputation_mere_id is None
