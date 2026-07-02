from rest_framework import serializers

from .models import DocumentBudget

MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
           'août', 'septembre', 'octobre', 'novembre', 'décembre']


class DocumentBudgetSerializer(serializers.ModelSerializer):
    """Forme frontend : { titre, type, date, pdf }."""

    date = serializers.SerializerMethodField()
    pdf = serializers.SerializerMethodField()

    class Meta:
        model = DocumentBudget
        fields = ['titre', 'type', 'date', 'pdf']

    def get_date(self, obj):
        if not obj.date:
            return ''
        return f'{obj.date.day} {MOIS_FR[obj.date.month - 1]} {obj.date.year}'

    def get_pdf(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return obj.lien or '#'
