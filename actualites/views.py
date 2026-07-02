from django.db.models import Count
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Actualite, NumeroRevue
from .serializers import ActualiteSerializer, NumeroRevueSerializer


class ActualiteListView(generics.ListAPIView):
    """GET /api/actualites/ — actualités actives, de la plus récente à la plus ancienne."""

    serializer_class = ActualiteSerializer

    def get_queryset(self):
        return Actualite.objects.filter(actif=True).order_by('-date', '-id')


class RevueAnneesView(APIView):
    """GET /api/revue-presse/annees/ — années + nombre de numéros.

    Forme : { annees: [{ annee, n }] } (alimente YearArchive).
    """

    def get(self, request):
        qs = (
            NumeroRevue.objects
            .filter(actif=True)
            .values('annee')
            .annotate(n=Count('id'))
            .order_by('-annee')
        )
        annees = [{'annee': row['annee'], 'n': row['n']} for row in qs]
        return Response({'annees': annees})


class RevueNumerosView(APIView):
    """GET /api/revue-presse/<annee>/ — numéros d'une année."""

    def get(self, request, annee):
        numeros = (
            NumeroRevue.objects
            .filter(annee=annee, actif=True)
            .order_by('ordre', 'id')
        )
        data = NumeroRevueSerializer(numeros, many=True, context={'request': request}).data
        return Response({'annee': annee, 'numeros': data})
