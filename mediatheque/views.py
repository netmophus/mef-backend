from rest_framework import generics

from .models import Photo, Video
from .serializers import PhotoSerializer, VideoSerializer


class PhotoListView(generics.ListAPIView):
    """GET /api/mediatheque/photos/ — photos actives, ordonnées."""

    serializer_class = PhotoSerializer

    def get_queryset(self):
        return Photo.objects.filter(actif=True).order_by('ordre', 'id')


class VideoListView(generics.ListAPIView):
    """GET /api/mediatheque/videos/ — vidéos actives, ordonnées."""

    serializer_class = VideoSerializer

    def get_queryset(self):
        return Video.objects.filter(actif=True).order_by('ordre', 'id')
