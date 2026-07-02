from rest_framework import generics

from .models import Publication
from .serializers import PublicationSerializer


class PublicationListView(generics.ListAPIView):
    """GET /api/publications/<rubrique>/ — publications actives d'une rubrique."""

    serializer_class = PublicationSerializer

    def get_queryset(self):
        return Publication.objects.filter(
            rubrique=self.kwargs['rubrique'], actif=True
        ).order_by('ordre', 'id')
