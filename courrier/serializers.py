from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from comptes.models import Direction
from .models import Registre, Correspondant, Courrier, EvenementCourrier, Imputation
from .services import valider_scan, generer_numero, calculer_sha256, journaliser

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

    class Meta:
        model = Courrier
        fields = ['id', 'numero_ordre', 'date_arrivee', 'correspondant_nom',
                  'objet', 'statut', 'statut_libelle', 'confidentialite']


class CourrierDetailSerializer(serializers.ModelSerializer):
    correspondant = CorrespondantSerializer(read_only=True)
    registre = serializers.CharField(source='registre.code', read_only=True)
    statut_libelle = serializers.CharField(source='get_statut_display', read_only=True)
    enregistre_par = serializers.SerializerMethodField()
    evenements = EvenementCourrierSerializer(many=True, read_only=True)
    imputations = serializers.SerializerMethodField()
    scan_url = serializers.SerializerMethodField()
    a_scan = serializers.SerializerMethodField()

    class Meta:
        model = Courrier
        fields = ['id', 'numero_ordre', 'registre', 'sens', 'date_document', 'date_arrivee',
                  'correspondant', 'objet', 'confidentialite', 'nombre_pieces', 'delai_reponse',
                  'statut', 'statut_libelle', 'hash_sha256', 'a_scan', 'scan_url',
                  'enregistre_par', 'cree_le', 'modifie_le', 'imputations', 'evenements']

    def get_imputations(self, obj):
        racines = [i for i in obj.imputations.all()
                   if i.annulee_le is None and i.imputation_mere_id is None]
        return ImputationSerializer(racines, many=True, context=self.context).data

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
