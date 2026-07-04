from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from comptes.models import Direction
from comptes.permissions import MotDePasseAJour, AvecPermission, AvecAuMoinsUne
from .models import Courrier, Correspondant, Imputation
from .serializers import (
    CourrierListSerializer, CourrierDetailSerializer,
    CourrierCreateSerializer, CourrierUpdateSerializer, CorrespondantSerializer,
    ImputationSerializer, ImputationCreateSerializer,
)
from .services import (
    journaliser, creer_imputation, accuser_imputation, traiter_imputation,
    annuler_imputation, ConflitImputation,
)

# Permissions donnant un droit de lecture sur les courriers (large ou directionnel).
LECTURE = [
    'courrier.consulter_courrier', 'courrier.imputer_premier_niveau',
    'courrier.accuser_reception', 'courrier.imputer_sous_arbre',
]


class CourrierPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def _peut_voir_confidentiel(user, courrier):
    if courrier.confidentialite != 'CONFIDENTIEL':
        return True
    return user.has_perm('courrier.consulter_confidentiel') or courrier.enregistre_par_id == user.id


class CourrierViewSet(ModelViewSet):
    """/api/v1/courriers/ — courrier arrivée (C1) + imputations (C2)."""

    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    pagination_class = CourrierPagination

    def get_permissions(self):
        if self.action == 'create':
            return [MotDePasseAJour(), AvecPermission('courrier.enregistrer_courrier')()]
        if self.action == 'partial_update':
            return [MotDePasseAJour(), AvecPermission('courrier.modifier_courrier')()]
        if self.action == 'classer':
            return [MotDePasseAJour(), AvecPermission('courrier.classer_courrier')()]
        if self.action == 'imputations':
            return [MotDePasseAJour(), AvecAuMoinsUne('courrier.imputer_premier_niveau', 'courrier.imputer_sous_arbre')()]
        # list, retrieve, scan
        return [MotDePasseAJour(), AvecAuMoinsUne(*LECTURE)()]

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
              .prefetch_related('evenements', 'evenements__acteur',
                                'imputations', 'imputations__direction_cible',
                                'imputations__impute_par', 'imputations__accuse_par'))

        if user.has_perm('courrier.consulter_courrier'):
            # Lecture large (BO, lecture centrale, imputation centrale).
            visibles = qs
        else:
            # Lecture directionnelle (secrétariat) : courriers imputés à son sous-arbre.
            dir_ids = user.direction.descendant_ids() if getattr(user, 'direction_id', None) else []
            visibles = qs.filter(
                Q(enregistre_par=user)
                | Q(imputations__direction_cible_id__in=dir_ids, imputations__annulee_le__isnull=True)
            ).distinct()

        if not user.has_perm('courrier.consulter_confidentiel'):
            visibles = visibles.filter(Q(confidentialite='ORDINAIRE') | Q(enregistre_par=user))

        p = self.request.query_params
        if p.get('registre'):
            visibles = visibles.filter(registre__code=p['registre'])
        if p.get('correspondant'):
            visibles = visibles.filter(correspondant_id=p['correspondant'])
        if p.get('statut'):
            visibles = visibles.filter(statut=p['statut'])
        if p.get('confidentialite'):
            visibles = visibles.filter(confidentialite=p['confidentialite'])
        if p.get('date_arrivee_min'):
            visibles = visibles.filter(date_arrivee__gte=p['date_arrivee_min'])
        if p.get('date_arrivee_max'):
            visibles = visibles.filter(date_arrivee__lte=p['date_arrivee_max'])
        q = (p.get('q') or '').strip()
        if q:
            visibles = visibles.filter(
                Q(numero_ordre__icontains=q) | Q(objet__icontains=q) | Q(correspondant__nom__icontains=q))
        return visibles

    def create(self, request, *args, **kwargs):
        ser = CourrierCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        courrier = ser.save()
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = CourrierUpdateSerializer(instance, data=request.data, partial=True, context={'request': request})
        ser.is_valid(raise_exception=True)
        courrier = ser.save()
        courrier = self.get_queryset().get(pk=courrier.pk)
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def classer(self, request, pk=None):
        courrier = self.get_object()
        if courrier.statut not in ('ENREGISTRE', 'TRAITE'):
            return Response({'detail': "Ce courrier ne peut pas être classé dans son état actuel."},
                            status=status.HTTP_409_CONFLICT)
        courrier.statut = 'CLASSE'
        courrier.save(update_fields=['statut', 'modifie_le'])
        journaliser(courrier, 'CLASSEMENT', request.user)
        courrier = self.get_queryset().get(pk=courrier.pk)
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='imputations')
    def imputations(self, request, pk=None):
        ser = ImputationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        mere = ser.validated_data.get('imputation_mere')
        user = request.user

        # Contrôle de permission AVANT get_object (sinon un secrétariat non
        # habilité obtiendrait 404 sur un courrier hors de son périmètre).
        if mere is None:
            if not user.has_perm('courrier.imputer_premier_niveau'):
                raise PermissionDenied("Imputation de premier niveau non autorisée.")
        elif not user.has_perm('courrier.imputer_sous_arbre'):
            raise PermissionDenied('Sous-imputation non autorisée.')

        courrier = self.get_object()

        if mere is not None:
            if mere.courrier_id != courrier.id:
                return Response({'detail': "L'imputation mère n'appartient pas à ce courrier."}, status=400)
            if not user.direction_id or user.direction_id not in mere.direction_cible.descendant_ids():
                raise PermissionDenied('Vous ne pouvez sous-imputer que dans le périmètre de votre direction.')

        try:
            creer_imputation(
                courrier, direction_cible=ser.validated_data['direction_cible'],
                instruction=ser.validated_data['instruction'],
                delai=ser.validated_data.get('delai'),
                commentaire=ser.validated_data.get('commentaire', ''),
                impute_par=user, imputation_mere=mere)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)

        courrier = self.get_queryset().get(pk=courrier.pk)
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def scan(self, request, pk=None):
        courrier = get_object_or_404(Courrier, pk=pk)
        # Doit être visible (lecture large ou directionnelle) ET autorisé si confidentiel.
        if not self.get_queryset().filter(pk=courrier.pk).exists():
            raise PermissionDenied('Accès non autorisé à ce courrier.')
        if not _peut_voir_confidentiel(request.user, courrier):
            raise PermissionDenied('Accès non autorisé à ce document confidentiel.')
        if not courrier.scan:
            raise Http404('Aucun scan pour ce courrier.')
        reponse = FileResponse(courrier.scan.open('rb'), content_type='application/pdf')
        reponse['Content-Disposition'] = f'inline; filename="{courrier.numero_ordre}.pdf"'
        # Cadre autorisé UNIQUEMENT depuis l'intranet : on exempte cette vue du
        # X-Frame-Options global (DENY) et on cible via CSP frame-ancestors.
        reponse.xframe_options_exempt = True
        reponse['Content-Security-Policy'] = f'frame-ancestors {settings.INTRANET_URL}'
        return reponse


class CorrespondantViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
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


class ImputationViewSet(GenericViewSet):
    """/api/v1/imputations/{id}/ — accuser / traiter / annuler."""

    queryset = Imputation.objects.all()

    def get_object(self):
        return get_object_or_404(
            Imputation.objects.select_related('courrier', 'direction_cible'), pk=self.kwargs['pk'])

    def get_permissions(self):
        if self.action == 'accuser':
            return [IsAuthenticated(), MotDePasseAJour(), AvecPermission('courrier.accuser_reception')()]
        if self.action == 'traiter':
            return [IsAuthenticated(), MotDePasseAJour(), AvecPermission('courrier.marquer_traite')()]
        return [IsAuthenticated(), MotDePasseAJour()]  # annuler : contrôle auteur dans l'action

    def _reponse(self, imp, request):
        imp = get_object_or_404(Imputation, pk=imp.pk)
        return Response(ImputationSerializer(imp, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def accuser(self, request, pk=None):
        imp = self.get_object()
        if request.user.direction_id != imp.direction_cible_id:
            raise PermissionDenied("L'accusé de réception relève du secrétariat de la direction cible.")
        try:
            accuser_imputation(imp, request.user)
        except ConflitImputation as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        return self._reponse(imp, request)

    @action(detail=True, methods=['post'])
    def traiter(self, request, pk=None):
        imp = self.get_object()
        if request.user.direction_id != imp.direction_cible_id:
            raise PermissionDenied('Le traitement relève du secrétariat de la direction cible.')
        try:
            traiter_imputation(imp, request.user, request.data.get('commentaire', ''))
        except ConflitImputation as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        return self._reponse(imp, request)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        imp = self.get_object()
        if imp.impute_par_id != request.user.id:
            raise PermissionDenied("Seul l'auteur de l'imputation peut l'annuler.")
        try:
            annuler_imputation(imp, request.user)
        except ConflitImputation as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        return Response({'detail': 'Imputation annulée.'})


def _anciennete(d):
    if d is None:
        return None
    if hasattr(d, 'date'):
        d = d.date()
    return (timezone.localdate() - d).days


def _item_courrier(c):
    return {
        'id': c.id, 'numero_ordre': c.numero_ordre, 'correspondant': c.correspondant.nom,
        'objet': c.objet, 'confidentialite': c.confidentialite, 'date_arrivee': c.date_arrivee,
        'statut': c.statut, 'anciennete_jours': _anciennete(c.date_arrivee),
    }


def _item_imputation(i):
    return {
        'imputation_id': i.id, 'courrier': _item_courrier(i.courrier),
        'instruction': i.instruction, 'instruction_libelle': i.get_instruction_display(),
        'direction_cible': i.direction_cible.sigle, 'delai': i.delai, 'statut': i.statut,
        'anciennete_jours': _anciennete(i.date_imputation),
    }


class DirectionListView(APIView):
    """GET /api/v1/directions/ — directions (pour l'autocomplétion d'imputation)."""

    def get_permissions(self):
        return [MotDePasseAJour(), AvecAuMoinsUne('courrier.imputer_premier_niveau', 'courrier.imputer_sous_arbre')()]

    def get(self, request):
        directions = Direction.objects.select_related('parent').all()
        data = [{'id': d.id, 'sigle': d.sigle, 'nom': d.nom,
                 'parent': d.parent.sigle if d.parent_id else None} for d in directions]
        return Response(data)


class BannetteView(APIView):
    """GET /api/v1/bannette/ — vue de travail par acteur (central / secrétariat)."""

    def get_permissions(self):
        return [MotDePasseAJour(), AvecAuMoinsUne('courrier.imputer_premier_niveau', 'courrier.accuser_reception')()]

    def get(self, request):
        user = request.user
        data = {'roles': list(user.groups.values_list('name', flat=True))}

        if user.has_perm('courrier.imputer_premier_niveau'):
            a_imputer = Courrier.objects.filter(statut='ENREGISTRE').select_related('correspondant')
            if not user.has_perm('courrier.consulter_confidentiel'):
                a_imputer = a_imputer.filter(Q(confidentialite='ORDINAIRE') | Q(enregistre_par=user))
            a_imputer = a_imputer.order_by('date_arrivee', 'numero_ordre')
            suivi = (Imputation.objects
                     .filter(imputation_mere__isnull=True, annulee_le__isnull=True, statut='EN_ATTENTE_ACCUSE')
                     .select_related('courrier', 'courrier__correspondant', 'direction_cible'))
            data['a_imputer'] = [_item_courrier(c) for c in a_imputer]
            data['suivi'] = [_item_imputation(i) for i in suivi]

        if user.has_perm('courrier.accuser_reception') and user.direction_id:
            base = (Imputation.objects
                    .filter(annulee_le__isnull=True, direction_cible=user.direction)
                    .select_related('courrier', 'courrier__correspondant', 'direction_cible'))
            data['a_accuser'] = [_item_imputation(i) for i in base.filter(statut='EN_ATTENTE_ACCUSE')]
            data['en_cours'] = [_item_imputation(i) for i in base.filter(statut='ACCUSEE')]
            data['traites'] = [_item_imputation(i) for i in base.filter(statut='TRAITEE')]

        return Response(data)
