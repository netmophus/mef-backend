from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Ministre, MembreCabinet, Discours, AlbumPhoto, Evenement,
    Denomination, MinistreHistorique, TexteOrganisation,
)
from .serializers import (
    MinistreSerializer, BiographieSerializer,
    MembreCabinetSerializer, DiscoursSerializer, AlbumPhotoSerializer,
    EvenementSerializer, DenominationSerializer, MinistreHistoriqueSerializer,
    TexteOrganisationSerializer,
)


class MinistreView(APIView):
    """GET /api/ministre/ — identité du Ministre + liens (bloc d'accueil)."""

    permission_classes = [AllowAny]  # site public

    def get(self, request):
        ministre = Ministre.load()
        data = MinistreSerializer(ministre, context={'request': request}).data
        return Response(data)


class BiographieView(APIView):
    """GET /api/ministre/biographie/ — biographie complète du Ministre."""

    permission_classes = [AllowAny]  # site public

    def get(self, request):
        ministre = Ministre.load()
        data = BiographieSerializer(ministre, context={'request': request}).data
        return Response(data)


class CabinetListView(generics.ListAPIView):
    """GET /api/cabinet/ — membres actifs du cabinet, ordonnés."""

    permission_classes = [AllowAny]  # site public
    serializer_class = MembreCabinetSerializer

    def get_queryset(self):
        return MembreCabinet.objects.filter(actif=True).order_by('ordre', 'id')


class DiscoursListView(generics.ListAPIView):
    """GET /api/discours/ — discours actifs, du plus récent au plus ancien."""

    permission_classes = [AllowAny]  # site public
    serializer_class = DiscoursSerializer

    def get_queryset(self):
        return Discours.objects.filter(actif=True).order_by('-date', '-id')


class AlbumListView(generics.ListAPIView):
    """GET /api/album-ministre/ — photos de l'album du Ministre, ordonnées."""

    permission_classes = [AllowAny]  # site public
    serializer_class = AlbumPhotoSerializer

    def get_queryset(self):
        return AlbumPhoto.objects.filter(actif=True).order_by('ordre', 'id')


class EvenementListView(generics.ListAPIView):
    """GET /api/evenements/ — événements de l'agenda, du plus récent au plus ancien."""

    permission_classes = [AllowAny]  # site public
    serializer_class = EvenementSerializer

    def get_queryset(self):
        return Evenement.objects.filter(actif=True).order_by('-date_debut', '-id')


class DenominationListView(generics.ListAPIView):
    """GET /api/historique/denominations/ — dénominations successives (frise)."""

    permission_classes = [AllowAny]  # site public
    serializer_class = DenominationSerializer

    def get_queryset(self):
        return Denomination.objects.filter(actif=True).order_by('ordre', 'id')


class MinistresHistoriqueListView(generics.ListAPIView):
    """GET /api/historique/ministres/ — galerie des ministres des Finances."""

    permission_classes = [AllowAny]  # site public
    serializer_class = MinistreHistoriqueSerializer

    def get_queryset(self):
        return MinistreHistorique.objects.filter(
            categorie='ministre', actif=True).order_by('ordre', 'id')


class DeleguesHistoriqueListView(generics.ListAPIView):
    """GET /api/historique/ministres-delegues/ — galerie des ministres délégués & SE."""

    permission_classes = [AllowAny]  # site public
    serializer_class = MinistreHistoriqueSerializer

    def get_queryset(self):
        return MinistreHistorique.objects.filter(
            categorie='delegue', actif=True).order_by('ordre', 'id')


class TexteOrganisationListView(generics.ListAPIView):
    """GET /api/historique/textes-organisation/ — décrets d'organisation."""

    permission_classes = [AllowAny]  # site public
    serializer_class = TexteOrganisationSerializer

    def get_queryset(self):
        return TexteOrganisation.objects.filter(actif=True).order_by('ordre', 'id')
