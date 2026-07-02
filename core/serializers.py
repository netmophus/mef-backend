from rest_framework import serializers

from .models import SiteConfig, MenuItem, LienUtile, Partenaire, BlocReforme


class SiteSerializer(serializers.ModelSerializer):
    """Identité du site (en-tête). `logo` renvoyé en URL absolue."""

    sousTitre = serializers.CharField(source='sous_titre')
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SiteConfig
        fields = ['nom', 'sousTitre', 'logo']

    def get_logo(self, obj):
        if not obj.logo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url


class ContactSerializer(serializers.ModelSerializer):
    """Coordonnées + réseaux sociaux (barre utilitaire)."""

    class Meta:
        model = SiteConfig
        fields = ['telephone', 'email', 'adresse', 'facebook', 'twitter', 'youtube']


class MenuItemSerializer(serializers.ModelSerializer):
    """Item de menu avec ses sous-entrées (récursif).

    Forme renvoyée : { label, path, submenu } — identique à l'ancien
    menuConfig.js (`submenu` vaut null pour un simple lien).
    """

    submenu = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['label', 'path', 'submenu']

    def get_submenu(self, obj):
        enfants = obj.enfants.filter(visible=True).order_by('ordre', 'id')
        if not enfants:
            return None
        return MenuItemSerializer(enfants, many=True, context=self.context).data


class LienUtileSerializer(serializers.ModelSerializer):
    """Forme frontend : { label, href }."""

    href = serializers.CharField(source='url')

    class Meta:
        model = LienUtile
        fields = ['label', 'href']


class PartenaireSerializer(serializers.ModelSerializer):
    """Forme frontend : { nom, sigle, init, logo, href }."""

    init = serializers.CharField(source='initiales')
    href = serializers.CharField(source='url')
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Partenaire
        fields = ['nom', 'sigle', 'init', 'logo', 'href']

    def get_logo(self, obj):
        if not obj.logo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url


class BlocReformeSerializer(serializers.ModelSerializer):
    """Forme frontend : { etiquette, titre, texte, bouton_label, bouton_href, src }."""

    bouton_href = serializers.CharField(source='bouton_url')
    src = serializers.SerializerMethodField()

    class Meta:
        model = BlocReforme
        fields = ['etiquette', 'titre', 'texte', 'bouton_label', 'bouton_href', 'src']

    def get_src(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url or None
