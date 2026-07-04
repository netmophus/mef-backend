from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Slide, QuickLink
from .serializers import SlideSerializer, QuickLinkSerializer


class SlideListView(generics.ListAPIView):
    """GET /api/slides/ — slides actifs du carrousel d'accueil, ordonnés."""

    permission_classes = [AllowAny]  # site public
    serializer_class = SlideSerializer

    def get_queryset(self):
        return Slide.objects.filter(actif=True).order_by('ordre', 'id')


class QuickLinkListView(generics.ListAPIView):
    """GET /api/quick-links/ — boutons « Accès rapides » actifs, ordonnés."""

    permission_classes = [AllowAny]  # site public
    serializer_class = QuickLinkSerializer

    def get_queryset(self):
        return QuickLink.objects.filter(actif=True).order_by('ordre', 'id')
