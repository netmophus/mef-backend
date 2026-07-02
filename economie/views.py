from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IndicateurMacro, IndicateurCle
from .serializers import IndicateurMacroSerializer, IndicateurCleSerializer


class IndicateursView(APIView):
    """GET /api/indicateurs/ — indicateurs macroéconomiques.

    Forme : { grands: [...], cles: [...] }.
    """

    def get(self, request):
        grands = IndicateurMacro.objects.filter(actif=True).order_by('ordre', 'id')
        cles = IndicateurCle.objects.filter(actif=True).order_by('ordre', 'id')
        return Response({
            'grands': IndicateurMacroSerializer(grands, many=True).data,
            'cles': IndicateurCleSerializer(cles, many=True).data,
        })
