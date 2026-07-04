from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Photo, Video
from .serializers import PhotoSerializer, VideoSerializer


class PhotoListView(generics.ListAPIView):
    """GET /api/mediatheque/photos/ — photos actives, ordonnées."""

    permission_classes = [AllowAny]  # site public
    serializer_class = PhotoSerializer

    def get_queryset(self):
        return Photo.objects.filter(actif=True).order_by('ordre', 'id')


class VideoListView(generics.ListAPIView):
    """GET /api/mediatheque/videos/ — vidéos actives, ordonnées."""

    permission_classes = [AllowAny]  # site public
    serializer_class = VideoSerializer

    def get_queryset(self):
        return Video.objects.filter(actif=True).order_by('ordre', 'id')
