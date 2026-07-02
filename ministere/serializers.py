from django.utils import timezone
from rest_framework import serializers

from .models import (
    Ministre, MinistreLien, MinistreRepere, MinistreParcours,
    MembreCabinet, Discours, AlbumPhoto, Evenement,
    Denomination, MinistreHistorique, TexteOrganisation,
)

MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
           'août', 'septembre', 'octobre', 'novembre', 'décembre']


def _lignes(texte):
    """Découpe un texte multi-lignes en liste (lignes vides ignorées)."""
    return [l.strip() for l in (texte or '').splitlines() if l.strip()]


def _date_fr(d):
    """Formate une date en français : « 12 juin 2026 »."""
    return f'{d.day} {MOIS_FR[d.month - 1]} {d.year}' if d else ''


class MinistreLienSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinistreLien
        fields = ['label', 'icone', 'href']


class MinistreRepereSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinistreRepere
        fields = ['icone', 'texte']


class MinistreParcoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinistreParcours
        fields = ['periode', 'titre', 'detail']


class MinistreSerializer(serializers.ModelSerializer):
    """Forme : { nom, fonction, image, etiquette, liens:[{label,icone,href}] }."""

    image = serializers.SerializerMethodField()
    liens = serializers.SerializerMethodField()

    class Meta:
        model = Ministre
        fields = ['nom', 'fonction', 'image', 'etiquette', 'liens']

    def get_image(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url

    def get_liens(self, obj):
        liens = MinistreLien.objects.filter(actif=True).order_by('ordre', 'id')
        return MinistreLienSerializer(liens, many=True, context=self.context).data


class BiographieSerializer(serializers.ModelSerializer):
    """Page biographie complète : { nom, fonction, image, reperes, presentation,
    formation, parcours, experience, conseils:{periode, liste} }."""

    nom = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    reperes = serializers.SerializerMethodField()
    presentation = serializers.SerializerMethodField()
    formation = serializers.SerializerMethodField()
    parcours = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    conseils = serializers.SerializerMethodField()

    class Meta:
        model = Ministre
        fields = ['nom', 'fonction', 'image', 'reperes', 'presentation',
                  'formation', 'parcours', 'experience', 'conseils']

    def get_nom(self, obj):
        return obj.nom_complet or obj.nom

    def get_image(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url

    def get_reperes(self, obj):
        qs = obj.reperes.order_by('ordre', 'id')
        return MinistreRepereSerializer(qs, many=True, context=self.context).data

    def get_presentation(self, obj):
        return {'accroche': obj.presentation_accroche, 'corps': obj.presentation_corps}

    def get_formation(self, obj):
        qs = obj.parcours.filter(categorie='formation').order_by('ordre', 'id')
        return MinistreParcoursSerializer(qs, many=True, context=self.context).data

    def get_parcours(self, obj):
        qs = obj.parcours.filter(categorie='professionnel').order_by('ordre', 'id')
        return MinistreParcoursSerializer(qs, many=True, context=self.context).data

    def get_experience(self, obj):
        return _lignes(obj.experience)

    def get_conseils(self, obj):
        return {'periode': obj.conseils_periode, 'liste': _lignes(obj.conseils)}


class MembreCabinetSerializer(serializers.ModelSerializer):
    """Forme : { nom, fonction, photo }."""

    photo = serializers.SerializerMethodField()

    class Meta:
        model = MembreCabinet
        fields = ['nom', 'fonction', 'photo']

    def get_photo(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url


class DiscoursSerializer(serializers.ModelSerializer):
    """Forme : { titre, date (FR), extrait, pdf }."""

    date = serializers.SerializerMethodField()
    pdf = serializers.SerializerMethodField()

    class Meta:
        model = Discours
        fields = ['titre', 'date', 'extrait', 'pdf']

    def get_date(self, obj):
        return _date_fr(obj.date)

    def get_pdf(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return obj.lien or None


class AlbumPhotoSerializer(serializers.ModelSerializer):
    """Forme attendue par le frontend : { titre, src, categorie, date }."""

    src = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = AlbumPhoto
        fields = ['titre', 'src', 'categorie', 'date']

    def get_src(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url or None

    def get_date(self, obj):
        if not obj.date:
            return ''
        return f'{MOIS_FR[obj.date.month - 1].capitalize()} {obj.date.year}'


class EvenementSerializer(serializers.ModelSerializer):
    """Forme frontend : { titre, type, date, date_iso, jour, mois, annee,
    heure, lieu, description, src, lien, a_la_une, passe }."""

    src = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    date_iso = serializers.SerializerMethodField()
    jour = serializers.SerializerMethodField()
    mois = serializers.SerializerMethodField()
    annee = serializers.SerializerMethodField()
    passe = serializers.SerializerMethodField()

    class Meta:
        model = Evenement
        fields = ['titre', 'type', 'date', 'date_iso', 'jour', 'mois', 'annee',
                  'heure', 'lieu', 'description', 'src', 'lien', 'a_la_une', 'passe']

    def get_src(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url or None

    def get_date(self, obj):
        if obj.date_fin and obj.date_fin != obj.date_debut:
            return f'{obj.date_debut.day} – {_date_fr(obj.date_fin)}'
        return _date_fr(obj.date_debut)

    def get_date_iso(self, obj):
        return obj.date_debut.isoformat()

    def get_jour(self, obj):
        return obj.date_debut.day

    def get_mois(self, obj):
        return MOIS_FR[obj.date_debut.month - 1].capitalize()

    def get_annee(self, obj):
        return obj.date_debut.year

    def get_passe(self, obj):
        fin = obj.date_fin or obj.date_debut
        return fin < timezone.localdate()


class DenominationSerializer(serializers.ModelSerializer):
    """Forme frontend : { an, nom }."""

    class Meta:
        model = Denomination
        fields = ['an', 'nom']


class MinistreHistoriqueSerializer(serializers.ModelSerializer):
    """Forme frontend : { nom, desc, image, secours }."""

    desc = serializers.CharField(source='description')
    image = serializers.SerializerMethodField()

    class Meta:
        model = MinistreHistorique
        fields = ['nom', 'desc', 'image', 'secours']

    def get_image(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return obj.photo_url or None


class TexteOrganisationSerializer(serializers.ModelSerializer):
    """Forme frontend : { titre, annee, href }."""

    href = serializers.SerializerMethodField()

    class Meta:
        model = TexteOrganisation
        fields = ['titre', 'annee', 'href']

    def get_href(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return obj.lien or '#'
