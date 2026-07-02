from rest_framework import serializers

from .models import Slide, QuickLink


class SlideSerializer(serializers.ModelSerializer):
    """Forme identique aux slides du frontend : { categorie, titre, texte,
    image, secours, position, cta:{label,href,icon}, cta2:{label,href}|null }.
    """

    image = serializers.SerializerMethodField()
    cta = serializers.SerializerMethodField()
    cta2 = serializers.SerializerMethodField()

    class Meta:
        model = Slide
        fields = ['categorie', 'titre', 'texte', 'image', 'secours', 'position', 'cta', 'cta2']

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

    def get_cta(self, obj):
        return {'label': obj.cta_label, 'href': obj.cta_href, 'icon': obj.cta_icon}

    def get_cta2(self, obj):
        if obj.cta2_label and obj.cta2_href:
            return {'label': obj.cta2_label, 'href': obj.cta2_href}
        return None


class QuickLinkSerializer(serializers.ModelSerializer):
    """Forme identique au frontend : { nom, icone, colors:[debut,fin], href }."""

    colors = serializers.SerializerMethodField()

    class Meta:
        model = QuickLink
        fields = ['nom', 'icone', 'colors', 'href']

    def get_colors(self, obj):
        return [obj.couleur_debut, obj.couleur_fin]
