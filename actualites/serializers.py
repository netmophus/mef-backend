from rest_framework import serializers

from .models import Actualite, NumeroRevue

MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
           'août', 'septembre', 'octobre', 'novembre', 'décembre']


def _date_fr(d):
    return f'{d.day} {MOIS_FR[d.month - 1]} {d.year}' if d else ''


def _lignes(texte):
    return [l.strip() for l in (texte or '').splitlines() if l.strip()]


class ActualiteSerializer(serializers.ModelSerializer):
    """Forme frontend : { id, titre, rubrique, date, date_iso, chapo,
    paragraphes, src, a_la_une }."""

    src = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    date_iso = serializers.SerializerMethodField()
    paragraphes = serializers.SerializerMethodField()

    class Meta:
        model = Actualite
        fields = ['id', 'titre', 'rubrique', 'date', 'date_iso', 'chapo',
                  'paragraphes', 'src', 'a_la_une']

    def get_src(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url or None

    def get_date(self, obj):
        return _date_fr(obj.date)

    def get_date_iso(self, obj):
        return obj.date.isoformat()

    def get_paragraphes(self, obj):
        return _lignes(obj.contenu)


class NumeroRevueSerializer(serializers.ModelSerializer):
    """Forme frontend : { titre, date, pdf }."""

    date = serializers.SerializerMethodField()
    pdf = serializers.SerializerMethodField()

    class Meta:
        model = NumeroRevue
        fields = ['titre', 'date', 'pdf']

    def get_date(self, obj):
        return _date_fr(obj.date)

    def get_pdf(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return obj.lien or '#'
