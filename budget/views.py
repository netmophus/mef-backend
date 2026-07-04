from django.db.models import Count
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DocumentBudget
from .serializers import DocumentBudgetSerializer


class BudgetAnneesView(APIView):
    """GET /api/budget/<rubrique>/annees/ — années + nombre de documents.

    Forme : { rubrique, annees: [{ annee, n }] } (de la plus récente à la plus
    ancienne). Alimente le composant YearArchive du frontend.
    """

    permission_classes = [AllowAny]  # site public

    def get(self, request, rubrique):
        qs = (
            DocumentBudget.objects
            .filter(rubrique=rubrique, actif=True)
            .values('annee')
            .annotate(n=Count('id'))
            .order_by('-annee')
        )
        annees = [{'annee': row['annee'], 'n': row['n']} for row in qs]
        return Response({'rubrique': rubrique, 'annees': annees})


class BudgetDocumentsView(APIView):
    """GET /api/budget/<rubrique>/<annee>/ — documents d'une rubrique pour une année."""

    permission_classes = [AllowAny]  # site public

    def get(self, request, rubrique, annee):
        docs = (
            DocumentBudget.objects
            .filter(rubrique=rubrique, annee=annee, actif=True)
            .order_by('ordre', 'id')
        )
        data = DocumentBudgetSerializer(docs, many=True, context={'request': request}).data
        return Response({'rubrique': rubrique, 'annee': annee, 'documents': data})
