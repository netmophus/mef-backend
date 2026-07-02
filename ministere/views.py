from rest_framework import generics
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

    def get(self, request):
        ministre = Ministre.load()
        data = MinistreSerializer(ministre, context={'request': request}).data
        return Response(data)


class BiographieView(APIView):
    """GET /api/ministre/biographie/ — biographie complète du Ministre."""

    def get(self, request):
        ministre = Ministre.load()
        data = BiographieSerializer(ministre, context={'request': request}).data
        return Response(data)


class CabinetListView(generics.ListAPIView):
    """GET /api/cabinet/ — membres actifs du cabinet, ordonnés."""

    serializer_class = MembreCabinetSerializer

    def get_queryset(self):
        return MembreCabinet.objects.filter(actif=True).order_by('ordre', 'id')


class DiscoursListView(generics.ListAPIView):
    """GET /api/discours/ — discours actifs, du plus récent au plus ancien."""

    serializer_class = DiscoursSerializer

    def get_queryset(self):
        return Discours.objects.filter(actif=True).order_by('-date', '-id')


class AlbumListView(generics.ListAPIView):
    """GET /api/album-ministre/ — photos de l'album du Ministre, ordonnées."""

    serializer_class = AlbumPhotoSerializer

    def get_queryset(self):
        return AlbumPhoto.objects.filter(actif=True).order_by('ordre', 'id')


class EvenementListView(generics.ListAPIView):
    """GET /api/evenements/ — événements de l'agenda, du plus récent au plus ancien."""

    serializer_class = EvenementSerializer

    def get_queryset(self):
        return Evenement.objects.filter(actif=True).order_by('-date_debut', '-id')


class DenominationListView(generics.ListAPIView):
    """GET /api/historique/denominations/ — dénominations successives (frise)."""

    serializer_class = DenominationSerializer

    def get_queryset(self):
        return Denomination.objects.filter(actif=True).order_by('ordre', 'id')


class MinistresHistoriqueListView(generics.ListAPIView):
    """GET /api/historique/ministres/ — galerie des ministres des Finances."""

    serializer_class = MinistreHistoriqueSerializer

    def get_queryset(self):
        return MinistreHistorique.objects.filter(
            categorie='ministre', actif=True).order_by('ordre', 'id')


class DeleguesHistoriqueListView(generics.ListAPIView):
    """GET /api/historique/ministres-delegues/ — galerie des ministres délégués & SE."""

    serializer_class = MinistreHistoriqueSerializer

    def get_queryset(self):
        return MinistreHistorique.objects.filter(
            categorie='delegue', actif=True).order_by('ordre', 'id')


class TexteOrganisationListView(generics.ListAPIView):
    """GET /api/historique/textes-organisation/ — décrets d'organisation."""

    serializer_class = TexteOrganisationSerializer

    def get_queryset(self):
        return TexteOrganisation.objects.filter(actif=True).order_by('ordre', 'id')
