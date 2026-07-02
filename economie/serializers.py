from rest_framework import serializers

from .models import IndicateurMacro, IndicateurCle


class IndicateurMacroSerializer(serializers.ModelSerializer):
    """Forme frontend : { label, value, decimals, suffix, unite, icone, couleurs }."""

    value = serializers.FloatField(source='valeur')
    decimals = serializers.IntegerField(source='decimales')
    suffix = serializers.CharField(source='suffixe')
    couleurs = serializers.SerializerMethodField()

    class Meta:
        model = IndicateurMacro
        fields = ['label', 'value', 'decimals', 'suffix', 'unite', 'icone', 'couleurs']

    def get_couleurs(self, obj):
        return [obj.couleur_debut, obj.couleur_fin]


class IndicateurCleSerializer(serializers.ModelSerializer):
    """Forme frontend : { label, value, max, color, note }."""

    value = serializers.FloatField(source='valeur')
    max = serializers.FloatField(source='maximum')
    color = serializers.CharField(source='couleur')

    class Meta:
        model = IndicateurCle
        fields = ['label', 'value', 'max', 'color', 'note']
