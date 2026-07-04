from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from comptes.models import Direction
from .models import Registre, Correspondant, Courrier, EvenementCourrier, Imputation
from .services import valider_scan, generer_numero, calculer_sha256, journaliser, creer_depart

DATE_FUTUR = "Cette date ne peut pas être dans le futur."


def _acteur(u):
    if not u:
        return None
    return {'matricule': u.matricule, 'nom_complet': u.get_full_name() or u.matricule}


class ImputationSerializer(serializers.ModelSerializer):
    """Imputation avec sa cascade (sous_imputations actives, récursif)."""

    direction_cible = serializers.SerializerMethodField()
    instruction_libelle = serializers.CharField(source='get_instruction_display', read_only=True)
    statut_libelle = serializers.CharField(source='get_statut_display', read_only=True)
    impute_par = serializers.SerializerMethodField()
    accuse_par = serializers.SerializerMethodField()
    sous_imputations = serializers.SerializerMethodField()

    class Meta:
        model = Imputation
        fields = ['id', 'direction_cible', 'instruction', 'instruction_libelle', 'delai',
                  'commentaire', 'impute_par', 'date_imputation', 'accuse_le', 'accuse_par',
                  'statut', 'statut_libelle', 'traite_le', 'commentaire_traitement', 'sous_imputations']

    def get_direction_cible(self, o):
        d = o.direction_cible
        return {'id': d.id, 'sigle': d.sigle, 'nom': d.nom}

    def get_impute_par(self, o):
        return _acteur(o.impute_par)

    def get_accuse_par(self, o):
        return _acteur(o.accuse_par) if o.accuse_par_id else None

    def get_sous_imputations(self, o):
        enfants = [i for i in o.sous_imputations.all() if i.annulee_le is None]
        return ImputationSerializer(enfants, many=True, context=self.context).data


class ImputationCreateSerializer(serializers.Serializer):
    direction_cible = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all())
    instruction = serializers.ChoiceField(choices=Imputation.INSTRUCTION)
    delai = serializers.DateField(required=False, allow_null=True)
    commentaire = serializers.CharField(max_length=500, required=False, allow_blank=True)
    imputation_mere = serializers.PrimaryKeyRelatedField(
        queryset=Imputation.objects.filter(annulee_le__isnull=True), required=False, allow_null=True)


class CorrespondantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Correspondant
        fields = ['id', 'nom', 'type', 'actif']


class EvenementCourrierSerializer(serializers.ModelSerializer):
    type_libelle = serializers.CharField(source='get_type_display', read_only=True)
    acteur = serializers.SerializerMethodField()

    class Meta:
        model = EvenementCourrier
        fields = ['id', 'type', 'type_libelle', 'acteur', 'horodatage', 'details']

    def get_acteur(self, obj):
        u = obj.acteur
        return {'matricule': u.matricule, 'nom_complet': u.get_full_name() or u.matricule}


class CourrierListSerializer(serializers.ModelSerializer):
    correspondant_nom = serializers.CharField(source='correspondant.nom', read_only=True)
    statut_libelle = serializers.CharField(source='get_statut_display', read_only=True)
    structure_emettrice = serializers.CharField(source='structure_emettrice.sigle', read_only=True, default=None)
    a_scan = serializers.SerializerMethodField()

    class Meta:
        model = Courrier
        fields = ['id', 'numero_ordre', 'sens', 'date_arrivee', 'correspondant_nom',
                  'objet', 'statut', 'statut_libelle', 'confidentialite',
                  # champs départ (null pour l'arrivée)
                  'reference_complete', 'structure_emettrice', 'date_signature',
                  'expedie_le', 'decharge_recue_le', 'a_scan']

    def get_a_scan(self, obj):
        return bool(obj.scan)


class CourrierDetailSerializer(serializers.ModelSerializer):
    correspondant = CorrespondantSerializer(read_only=True)
    registre = serializers.CharField(source='registre.code', read_only=True)
    statut_libelle = serializers.CharField(source='get_statut_display', read_only=True)
    enregistre_par = serializers.SerializerMethodField()
    evenements = EvenementCourrierSerializer(many=True, read_only=True)
    imputations = serializers.SerializerMethodField()
    scan_url = serializers.SerializerMethodField()
    a_scan = serializers.SerializerMethodField()
    # Départ (lot C4)
    structure_emettrice = serializers.SerializerMethodField()
    ampliations = serializers.SerializerMethodField()
    courrier_origine = serializers.SerializerMethodField()
    reponses_liees = serializers.SerializerMethodField()

    class Meta:
        model = Courrier
        fields = ['id', 'numero_ordre', 'registre', 'sens', 'date_document', 'date_arrivee',
                  'correspondant', 'objet', 'confidentialite', 'nombre_pieces', 'delai_reponse',
                  'statut', 'statut_libelle', 'hash_sha256', 'a_scan', 'scan_url',
                  'enregistre_par', 'cree_le', 'modifie_le', 'imputations', 'evenements',
                  # départ
                  'reference_complete', 'structure_emettrice', 'signataire_nom', 'signataire_qualite',
                  'date_signature', 'expedie_le', 'decharge_recue_le', 'decharge_commentaire',
                  'ampliations', 'courrier_origine', 'reponses_liees']

    def get_imputations(self, obj):
        racines = [i for i in obj.imputations.all()
                   if i.annulee_le is None and i.imputation_mere_id is None]
        return ImputationSerializer(racines, many=True, context=self.context).data

    def get_structure_emettrice(self, obj):
        d = obj.structure_emettrice
        return {'id': d.id, 'sigle': d.sigle, 'nom': d.nom} if d else None

    def get_ampliations(self, obj):
        return [{'id': c.correspondant.id, 'nom': c.correspondant.nom} for c in obj.copies.all()]

    def get_courrier_origine(self, obj):
        o = obj.courrier_origine
        if not o:
            return None
        return {'id': o.id, 'numero_ordre': o.numero_ordre, 'objet': o.objet, 'statut': o.statut}

    def get_reponses_liees(self, obj):
        return [{'id': r.id, 'numero_ordre': r.numero_ordre, 'reference_complete': r.reference_complete,
                 'date_signature': r.date_signature, 'decharge_recue_le': r.decharge_recue_le,
                 'expedie_le': r.expedie_le, 'statut': r.statut}
                for r in obj.reponses.all().order_by('id')]

    def get_enregistre_par(self, obj):
        u = obj.enregistre_par
        return {'matricule': u.matricule, 'nom_complet': u.get_full_name() or u.matricule}

    def get_a_scan(self, obj):
        return bool(obj.scan)

    def get_scan_url(self, obj):
        return f'/api/v1/courriers/{obj.id}/scan/' if obj.scan else None


class CourrierCreateSerializer(serializers.Serializer):
    """Enregistrement (multipart) — le numéro et le registre sont fixés côté serveur."""

    scan = serializers.FileField()
    date_document = serializers.DateField()
    date_arrivee = serializers.DateField(required=False)
    correspondant = serializers.PrimaryKeyRelatedField(queryset=Correspondant.objects.filter(actif=True))
    objet = serializers.CharField(max_length=500)
    confidentialite = serializers.ChoiceField(choices=Courrier.CONFIDENTIALITE, default='ORDINAIRE')
    nombre_pieces = serializers.IntegerField(min_value=1, default=1)
    delai_reponse = serializers.DateField(required=False, allow_null=True)

    def validate_date_document(self, v):
        if v > timezone.localdate():
            raise serializers.ValidationError(DATE_FUTUR)
        return v

    def validate_date_arrivee(self, v):
        if v > timezone.localdate():
            raise serializers.ValidationError(DATE_FUTUR)
        return v

    def validate_scan(self, fichier):
        try:
            valider_scan(fichier)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])
        return fichier

    def create(self, validated):
        request = self.context['request']
        registre = Registre.objects.get(code='ARR')  # C1 : courrier arrivée uniquement
        scan = validated['scan']
        numero = generer_numero(registre)
        courrier = Courrier(
            registre=registre, numero_ordre=numero, sens='ARRIVEE',
            enregistre_par=request.user,
            date_document=validated['date_document'],
            date_arrivee=validated.get('date_arrivee') or timezone.localdate(),
            correspondant=validated['correspondant'],
            objet=validated['objet'],
            confidentialite=validated.get('confidentialite', 'ORDINAIRE'),
            nombre_pieces=validated.get('nombre_pieces', 1),
            delai_reponse=validated.get('delai_reponse'),
        )
        courrier.hash_sha256 = calculer_sha256(scan)
        courrier.scan = scan  # le nom du fichier utilise numero_ordre (déjà fixé)
        courrier.save()
        journaliser(courrier, 'ENREGISTREMENT', request.user, {'numero_ordre': numero})
        return courrier


class CourrierDepartCreateSerializer(serializers.Serializer):
    """Enregistrement d'un courrier DÉPART signé (lot C4). Scan optionnel à la
    création (obligatoire à l'expédition) : l'agent enregistre pour obtenir la
    référence, la reporte sur l'original, puis scanne."""

    scan = serializers.FileField(required=False, allow_null=True)
    structure_emettrice = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all())
    objet = serializers.CharField(max_length=500)
    correspondant = serializers.PrimaryKeyRelatedField(queryset=Correspondant.objects.filter(actif=True))
    signataire_nom = serializers.CharField(max_length=150, required=False, allow_blank=True)
    signataire_qualite = serializers.CharField(max_length=100, required=False, allow_blank=True)
    date_signature = serializers.DateField(required=False, allow_null=True)
    nombre_pieces = serializers.IntegerField(min_value=1, default=1)
    confidentialite = serializers.ChoiceField(choices=Courrier.CONFIDENTIALITE, default='ORDINAIRE')
    ampliations = serializers.PrimaryKeyRelatedField(
        queryset=Correspondant.objects.filter(actif=True), many=True, required=False)
    courrier_origine = serializers.PrimaryKeyRelatedField(
        queryset=Courrier.objects.filter(sens='ARRIVEE'), required=False, allow_null=True)

    def validate_scan(self, fichier):
        if fichier is None:
            return fichier
        try:
            valider_scan(fichier)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])
        return fichier

    def validate_date_signature(self, v):
        if v and v > timezone.localdate():
            raise serializers.ValidationError(DATE_FUTUR)
        return v

    def create(self, validated):
        request = self.context['request']
        try:
            return creer_depart(
                enregistre_par=request.user,
                structure_emettrice=validated['structure_emettrice'],
                objet=validated['objet'], correspondant=validated['correspondant'],
                signataire_nom=validated.get('signataire_nom', ''),
                signataire_qualite=validated.get('signataire_qualite', ''),
                date_signature=validated.get('date_signature'),
                ampliations=validated.get('ampliations') or [],
                courrier_origine=validated.get('courrier_origine'),
                scan=validated.get('scan'),
                nombre_pieces=validated.get('nombre_pieces', 1),
                confidentialite=validated.get('confidentialite', 'ORDINAIRE'))
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])


class CourrierUpdateSerializer(serializers.ModelSerializer):
    """Modification des métadonnées (numero_ordre et registre restent immuables)."""

    class Meta:
        model = Courrier
        fields = ['objet', 'correspondant', 'date_document', 'date_arrivee',
                  'nombre_pieces', 'delai_reponse', 'confidentialite']

    def validate_date_document(self, v):
        if v > timezone.localdate():
            raise serializers.ValidationError(DATE_FUTUR)
        return v

    def validate_date_arrivee(self, v):
        if v > timezone.localdate():
            raise serializers.ValidationError(DATE_FUTUR)
        return v

    def update(self, instance, validated):
        request = self.context['request']
        avant, apres = {}, {}
        for champ, valeur in validated.items():
            ancienne = getattr(instance, champ)
            if champ == 'correspondant':
                if ancienne.id != valeur.id:
                    avant[champ], apres[champ] = ancienne.nom, valeur.nom
            elif ancienne != valeur:
                avant[champ], apres[champ] = str(ancienne), str(valeur)
            setattr(instance, champ, valeur)
        if avant:
            instance.save()
            journaliser(instance, 'MODIFICATION', request.user, {'avant': avant, 'apres': apres})
        return instance
