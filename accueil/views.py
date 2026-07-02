from rest_framework import generics

from .models import Slide, QuickLink
from .serializers import SlideSerializer, QuickLinkSerializer


class SlideListView(generics.ListAPIView):
    """GET /api/slides/ — slides actifs du carrousel d'accueil, ordonnés."""

    serializer_class = SlideSerializer

    def get_queryset(self):
        return Slide.objects.filter(actif=True).order_by('ordre', 'id')


class QuickLinkListView(generics.ListAPIView):
    """GET /api/quick-links/ — boutons « Accès rapides » actifs, ordonnés."""

    serializer_class = QuickLinkSerializer

    def get_queryset(self):
        return QuickLink.objects.filter(actif=True).order_by('ordre', 'id')
