from rest_framework import serializers

from .models import Photo, Video

MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
           'août', 'septembre', 'octobre', 'novembre', 'décembre']


def _date_fr(d):
    return f'{d.day} {MOIS_FR[d.month - 1]} {d.year}' if d else ''


class PhotoSerializer(serializers.ModelSerializer):
    """Forme frontend : { titre, src }."""

    src = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ['titre', 'src']

    def get_src(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url or None


class VideoSerializer(serializers.ModelSerializer):
    """Forme frontend : { titre, date, duree, secours, lien }."""

    date = serializers.SerializerMethodField()
    secours = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['titre', 'date', 'duree', 'secours', 'lien']

    def get_date(self, obj):
        return _date_fr(obj.date)

    def get_secours(self, obj):
        if obj.miniature:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.miniature.url) if request else obj.miniature.url
        return obj.miniature_url or None
