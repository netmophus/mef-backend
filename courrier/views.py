from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from comptes.permissions import MotDePasseAJour, AvecPermission
from .models import Courrier, Correspondant
from .serializers import (
    CourrierListSerializer, CourrierDetailSerializer,
    CourrierCreateSerializer, CourrierUpdateSerializer, CorrespondantSerializer,
)
from .services import journaliser


class CourrierPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def _peut_voir_confidentiel(user, courrier):
    """Un confidentiel n'est visible que si l'utilisateur a la permission dédiée
    OU s'il en est l'enregistreur."""
    if courrier.confidentialite != 'CONFIDENTIEL':
        return True
    return user.has_perm('courrier.consulter_confidentiel') or courrier.enregistre_par_id == user.id


class CourrierViewSet(ModelViewSet):
    """/api/v1/courriers/ — enregistrement, consultation, recherche, modification, classement."""

    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    pagination_class = CourrierPagination

    PERMS = {
        'create': 'courrier.enregistrer_courrier',
        'list': 'courrier.consulter_courrier',
        'retrieve': 'courrier.consulter_courrier',
        'scan': 'courrier.consulter_courrier',
        'partial_update': 'courrier.modifier_courrier',
        'classer': 'courrier.classer_courrier',
    }

    def get_permissions(self):
        codename = self.PERMS.get(self.action, 'courrier.consulter_courrier')
        return [MotDePasseAJour(), AvecPermission(codename)()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CourrierCreateSerializer
        if self.action == 'list':
            return CourrierListSerializer
        if self.action == 'partial_update':
            return CourrierUpdateSerializer
        return CourrierDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (Courrier.objects
              .select_related('correspondant', 'registre', 'enregistre_par')
              .prefetch_related('evenements', 'evenements__acteur'))

        # Visibilité transverse des confidentiels.
        if not user.has_perm('courrier.consulter_confidentiel'):
            qs = qs.filter(Q(confidentialite='ORDINAIRE') | Q(enregistre_par=user))

        p = self.request.query_params
        if p.get('registre'):
            qs = qs.filter(registre__code=p['registre'])
        if p.get('correspondant'):
            qs = qs.filter(correspondant_id=p['correspondant'])
        if p.get('statut'):
            qs = qs.filter(statut=p['statut'])
        if p.get('confidentialite'):
            qs = qs.filter(confidentialite=p['confidentialite'])
        if p.get('date_arrivee_min'):
            qs = qs.filter(date_arrivee__gte=p['date_arrivee_min'])
        if p.get('date_arrivee_max'):
            qs = qs.filter(date_arrivee__lte=p['date_arrivee_max'])
        q = (p.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(numero_ordre__icontains=q) | Q(objet__icontains=q) | Q(correspondant__nom__icontains=q))
        return qs

    def create(self, request, *args, **kwargs):
        ser = CourrierCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        courrier = ser.save()
        detail = CourrierDetailSerializer(courrier, context={'request': request}).data
        return Response(detail, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = CourrierUpdateSerializer(instance, data=request.data, partial=True,
                                       context={'request': request})
        ser.is_valid(raise_exception=True)
        courrier = ser.save()
        # Re-lecture fraîche : inclure l'éventuel événement MODIFICATION qui vient d'être créé.
        courrier = self.get_queryset().get(pk=courrier.pk)
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def classer(self, request, pk=None):
        courrier = self.get_object()
        if courrier.statut != 'ENREGISTRE':
            return Response(
                {'detail': "Seul un courrier au statut « Enregistré » peut être classé sans suite."},
                status=status.HTTP_409_CONFLICT)
        courrier.statut = 'CLASSE'
        courrier.save(update_fields=['statut', 'modifie_le'])
        journaliser(courrier, 'CLASSEMENT', request.user)
        courrier = self.get_queryset().get(pk=courrier.pk)  # inclure l'événement CLASSEMENT
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data)

    @action(detail=True, methods=['get'])
    def scan(self, request, pk=None):
        # Lecture hors queryset filtré pour renvoyer 403 (et non 404) sur un confidentiel non autorisé.
        courrier = get_object_or_404(Courrier, pk=pk)
        if not _peut_voir_confidentiel(request.user, courrier):
            raise PermissionDenied('Accès non autorisé à ce document confidentiel.')
        if not courrier.scan:
            raise Http404('Aucun scan pour ce courrier.')
        reponse = FileResponse(courrier.scan.open('rb'), content_type='application/pdf')
        reponse['Content-Disposition'] = f'inline; filename="{courrier.numero_ordre}.pdf"'
        return reponse


class CorrespondantViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    """/api/v1/courriers/correspondants/ — liste (autocomplétion) + création à la volée."""

    serializer_class = CorrespondantSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Correspondant.objects.filter(actif=True)
        q = (self.request.query_params.get('q') or '').strip()
        if q:
            qs = qs.filter(nom__icontains=q)
        return qs

    def get_permissions(self):
        codename = ('courrier.enregistrer_courrier' if self.action == 'create'
                    else 'courrier.consulter_courrier')
        return [MotDePasseAJour(), AvecPermission(codename)()]
