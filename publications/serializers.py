from rest_framework import serializers

from .models import Publication


class PublicationSerializer(serializers.ModelSerializer):
    """Forme frontend : { type, titre, pdf }."""

    pdf = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = ['type', 'titre', 'pdf']

    def get_pdf(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return obj.lien or '#'
