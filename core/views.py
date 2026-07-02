from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SiteConfig, MenuItem, LienUtile, Partenaire, BlocReforme
from .serializers import (
    SiteSerializer, ContactSerializer, MenuItemSerializer,
    LienUtileSerializer, PartenaireSerializer, BlocReformeSerializer,
)


class HeaderView(APIView):
    """GET /api/header/ — tout l'en-tête en un seul appel.

    Renvoie : { site, contact, menu } pour alimenter le Header du frontend.
    """

    def get(self, request):
        config = SiteConfig.load()
        menu_racine = (
            MenuItem.objects
            .filter(parent__isnull=True, visible=True)
            .order_by('ordre', 'id')
        )
        ctx = {'request': request}
        return Response({
            'site': SiteSerializer(config, context=ctx).data,
            'contact': ContactSerializer(config, context=ctx).data,
            'menu': MenuItemSerializer(menu_racine, many=True, context=ctx).data,
        })


class LiensPartenairesView(APIView):
    """GET /api/liens-partenaires/ — liens utiles + partenaires.

    Forme : { liens: [...], partenaires: [...] }.
    """

    def get(self, request):
        ctx = {'request': request}
        liens = LienUtile.objects.filter(actif=True).order_by('ordre', 'id')
        partenaires = Partenaire.objects.filter(actif=True).order_by('ordre', 'id')
        return Response({
            'liens': LienUtileSerializer(liens, many=True, context=ctx).data,
            'partenaires': PartenaireSerializer(partenaires, many=True, context=ctx).data,
            'reforme': BlocReformeSerializer(BlocReforme.load(), context=ctx).data,
        })
