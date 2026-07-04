from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.http import FileResponse, Http404, HttpResponse
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
    ImputationSerializer, ImputationCreateSerializer, CourrierDepartCreateSerializer,
)
from .services import (
    journaliser, creer_imputation, accuser_imputation, traiter_imputation,
    annuler_imputation, relancer_imputation, sous_imputations_ouvertes,
    expedier_courrier, decharger_courrier, calculer_sha256, valider_scan, ConflitImputation,
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
        if self.action in ('expedier', 'decharge', 'attacher_scan'):
            return [MotDePasseAJour(), AvecPermission('courrier.enregistrer_courrier')()]
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
              .select_related('correspondant', 'registre', 'enregistre_par', 'structure_emettrice')
              .prefetch_related('evenements', 'evenements__acteur',
                                'imputations', 'imputations__direction_cible',
                                'imputations__impute_par', 'imputations__accuse_par',
                                'copies__correspondant', 'reponses'))

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
        if p.get('sens'):
            visibles = visibles.filter(sens=p['sens'])
        if p.get('decharge') == 'absente':
            visibles = visibles.filter(sens='DEPART', expedie_le__isnull=False, decharge_recue_le__isnull=True)
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
        # Départ (C4) ou arrivée (C1) selon le sens déclaré.
        if request.data.get('sens') == 'DEPART':
            ser = CourrierDepartCreateSerializer(data=request.data, context={'request': request})
        else:
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

    def _detail(self, courrier, request):
        courrier = self.get_queryset().get(pk=courrier.pk)
        return Response(CourrierDetailSerializer(courrier, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def expedier(self, request, pk=None):
        depart = self.get_object()
        date_exp = parse_date(request.data.get('date') or '') if request.data.get('date') else None
        try:
            expedier_courrier(depart, request.user, date_exp)
        except ConflitImputation as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        return self._detail(depart, request)

    @action(detail=True, methods=['post'])
    def decharge(self, request, pk=None):
        depart = self.get_object()
        d = parse_date(request.data.get('date') or '')
        if not d:
            return Response({'detail': 'La date de décharge est requise.'}, status=400)
        try:
            decharger_courrier(depart, request.user, d, request.data.get('commentaire', ''))
        except ConflitImputation as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        return self._detail(depart, request)

    @action(detail=True, methods=['post'], url_path='attacher-scan')
    def attacher_scan(self, request, pk=None):
        depart = self.get_object()
        if depart.sens != 'DEPART':
            return Response({'detail': "Réservé aux courriers départ."}, status=400)
        fichier = request.FILES.get('scan')
        if not fichier:
            return Response({'detail': 'Le scan PDF est requis.'}, status=400)
        try:
            valider_scan(fichier)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        depart.hash_sha256 = calculer_sha256(fichier)
        depart.scan = fichier
        depart.save(update_fields=['scan', 'hash_sha256', 'modifie_le'])
        journaliser(depart, 'REMPLACEMENT_SCAN', request.user, {'attachement': True})
        return self._detail(depart, request)

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
        if self.action == 'relancer':
            return [IsAuthenticated(), MotDePasseAJour(), AvecPermission('courrier.voir_tableau_bord')()]
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
        clore = str(request.data.get('clore_sous', '')).lower() in ('true', '1', 'yes')
        # 0.2 : avertir si des sous-imputations sont encore ouvertes.
        ouvertes = sous_imputations_ouvertes(imp)
        if ouvertes and not clore:
            return Response({
                'code': 'SOUS_IMPUTATIONS_OUVERTES',
                'detail': 'Des sous-imputations sont encore ouvertes.',
                'sous_imputations': [{'id': s.id, 'direction_cible': s.direction_cible.sigle,
                                      'instruction': s.get_instruction_display()} for s in ouvertes],
            }, status=status.HTTP_409_CONFLICT)
        try:
            traiter_imputation(imp, request.user, request.data.get('commentaire', ''), clore_sous=clore)
        except ConflitImputation as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=400)
        return self._reponse(imp, request)

    @action(detail=True, methods=['post'])
    def relancer(self, request, pk=None):
        imp = self.get_object()
        user = request.user
        # Périmètre : central (imputer_premier_niveau) → tout ; secrétariat → son sous-arbre.
        if not user.has_perm('courrier.imputer_premier_niveau'):
            dir_ids = user.direction.descendant_ids() if user.direction_id else []
            if imp.direction_cible_id not in dir_ids:
                raise PermissionDenied("Cette imputation n'est pas dans votre périmètre.")
        try:
            relancer_imputation(imp, user, request.data.get('commentaire', ''))
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
        'derniere_relance_le': i.derniere_relance_le,
        'traite_le': i.traite_le,
    }


def _tri_bannette(items):
    """Les imputations relancées remontent en tête ; puis les plus anciennes."""
    return sorted(items, key=lambda x: (x['derniere_relance_le'] is None,
                                        -(x['anciennete_jours'] or 0)))


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
            data['suivi'] = _tri_bannette([_item_imputation(i) for i in suivi])

        if user.has_perm('courrier.accuser_reception') and user.direction_id:
            base = (Imputation.objects
                    .filter(annulee_le__isnull=True, direction_cible=user.direction)
                    .select_related('courrier', 'courrier__correspondant', 'direction_cible'))
            data['a_accuser'] = _tri_bannette([_item_imputation(i) for i in base.filter(statut='EN_ATTENTE_ACCUSE')])
            data['en_cours'] = _tri_bannette([_item_imputation(i) for i in base.filter(statut='ACCUSEE')])
            data['traites'] = [_item_imputation(i) for i in base.filter(statut='TRAITEE')]

        return Response(data)


# === Tableau de bord de pilotage (lot C3) ====================================

def _age_imputation(i, today):
    """Ancienneté : jours depuis date_imputation si non accusée, sinon accuse_le."""
    ref = i.accuse_le or i.date_imputation
    if hasattr(ref, 'date'):
        ref = ref.date()
    return (today - ref).days


def _direction_reporting(direction, racine_ids, dir_by_id):
    """Remonte jusqu'à la direction de « premier niveau » du périmètre.

    On s'arrête quand la direction courante EST une racine du périmètre, ou que
    son parent en est une (elle est alors une direction de 1er niveau)."""
    node = direction
    while (node.parent_id is not None and node.id not in racine_ids
           and node.parent_id not in racine_ids):
        node = dir_by_id[node.parent_id]
    return node


def _objet_visible(c, user):
    """Masque l'objet d'un courrier confidentiel pour qui n'y a pas droit."""
    if c.confidentialite == 'CONFIDENTIEL' and not (
            user.has_perm('courrier.consulter_confidentiel') or c.enregistre_par_id == user.id):
        return 'Pli confidentiel'
    return c.objet


def _ligne_pilotage(i, user, today):
    c = i.courrier
    return {
        'imputation_id': i.id,
        'courrier': {'id': c.id, 'numero': c.numero_ordre, 'objet': _objet_visible(c, user),
                     'correspondant': c.correspondant.nom},
        'direction_cible': i.direction_cible.sigle,
        'instruction': i.get_instruction_display(),
        'delai': i.delai,
        'jours_de_retard': (today - i.delai).days if i.delai else None,
        'derniere_relance_le': i.derniere_relance_le,
    }


class TableauBordView(APIView):
    """GET /api/v1/tableau-bord/ — pilotage du courrier arrivée.

    Central (imputer_premier_niveau) : tout le ministère.
    Secrétariat : restreint à son sous-arbre (même code, périmètre filtré)."""

    def get_permissions(self):
        return [MotDePasseAJour(), AvecPermission('courrier.voir_tableau_bord')()]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        central = user.has_perm('courrier.imputer_premier_niveau')

        if central:
            perimetre = 'Ministère'
            racine_ids = set(Direction.objects.filter(parent__isnull=True).values_list('id', flat=True))
            scope_ids = None  # aucun filtre
        else:
            direction = getattr(user, 'direction', None)
            perimetre = direction.sigle if direction else '—'
            racine_ids = {direction.id} if direction else set()
            scope_ids = set(direction.descendant_ids()) if direction else set()

        dir_by_id = {d.id: d for d in Direction.objects.select_related('parent').all()}

        # Imputations « actives » : non annulées, non traitées, courrier non classé.
        imps = (Imputation.objects
                .filter(annulee_le__isnull=True)
                .exclude(statut='TRAITEE')
                .exclude(courrier__statut='CLASSE')
                .select_related('courrier', 'courrier__correspondant', 'direction_cible', 'courrier__enregistre_par'))
        if scope_ids is not None:
            imps = imps.filter(direction_cible_id__in=scope_ids)
        imps = list(imps)

        # Agrégation par direction de reporting (1er niveau, sous-arbre agrégé).
        agg = {}
        for i in imps:
            rep = _direction_reporting(i.direction_cible, racine_ids, dir_by_id)
            a = agg.get(rep.id)
            if a is None:
                a = agg[rep.id] = {'direction': {'id': rep.id, 'sigle': rep.sigle},
                                   'actives': 0, 'en_retard': 0, '_ages': []}
            a['actives'] += 1
            a['_ages'].append(_age_imputation(i, today))
            if i.delai and i.delai < today:
                a['en_retard'] += 1
        par_direction = []
        for a in agg.values():
            ages = a.pop('_ages')
            a['age_moyen_jours'] = round(sum(ages) / len(ages), 1) if ages else 0
            a['plus_ancien_jours'] = max(ages) if ages else 0
            par_direction.append(a)
        par_direction.sort(key=lambda x: (-x['en_retard'], -x['actives']))

        retards = sorted(
            (_ligne_pilotage(i, user, today) for i in imps if i.delai and i.delai < today),
            key=lambda x: -x['jours_de_retard'])
        proches = sorted(
            (_ligne_pilotage(i, user, today) for i in imps
             if i.delai and today <= i.delai <= today + timedelta(days=3)),
            key=lambda x: x['delai'])

        if central:
            courriers_en_instance = Courrier.objects.exclude(statut__in=['TRAITE', 'CLASSE']).count()
        else:
            courriers_en_instance = len({i.courrier_id for i in imps})

        depuis_30j = timezone.now() - timedelta(days=30)
        traites_qs = Imputation.objects.filter(
            annulee_le__isnull=True, statut='TRAITEE', traite_le__gte=depuis_30j)
        if scope_ids is not None:
            traites_qs = traites_qs.filter(direction_cible_id__in=scope_ids)

        synthese = {
            'courriers_en_instance': courriers_en_instance,
            'imputations_en_attente_accuse': sum(1 for i in imps if i.statut == 'EN_ATTENTE_ACCUSE'),
            'en_retard': len(retards),
            'delais_sous_3j': len(proches),
            'traites_30j': traites_qs.count(),
        }

        return Response({
            'perimetre': perimetre,
            'central': central,
            'genere_le': timezone.now(),
            'synthese': synthese,
            'par_direction': par_direction,
            'retards': retards,
            'delais_proches': proches,
            'temps_moyens_30j': self._temps_moyens(scope_ids, depuis_30j),
        })

    def _temps_moyens(self, scope_ids, depuis):
        base = Imputation.objects.filter(annulee_le__isnull=True)
        if scope_ids is not None:
            base = base.filter(direction_cible_id__in=scope_ids)

        prem = base.filter(imputation_mere__isnull=True, date_imputation__gte=depuis).select_related('courrier')
        h_enr_imp = [(i.date_imputation - i.courrier.cree_le).total_seconds() / 3600 for i in prem]

        acc = base.filter(accuse_le__gte=depuis)
        h_imp_acc = [(i.accuse_le - i.date_imputation).total_seconds() / 3600 for i in acc]

        tr = base.filter(statut='TRAITEE', traite_le__gte=depuis, accuse_le__isnull=False)
        j_acc_tr = [(i.traite_le - i.accuse_le).total_seconds() / 86400 for i in tr]

        def moy(xs):
            return round(sum(xs) / len(xs), 1) if xs else None

        return {
            'enregistrement_vers_imputation_h': moy(h_enr_imp),
            'imputation_vers_accuse_h': moy(h_imp_acc),
            'accuse_vers_traite_jours': moy(j_acc_tr),
        }


# === Bordereau d'envoi (lot C4) ==============================================

def _bordereau_pdf(jour, departs):
    """Construit le PDF du bordereau des départs expédiés, groupés par correspondant."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm, title='Bordereau d\'envoi')
    styles = getSampleStyleSheet()
    h_min = ParagraphStyle('minist', parent=styles['Title'], fontSize=13, spaceAfter=2, textColor=colors.HexColor('#004080'))
    h_sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#5b6b7a'))
    h_corr = ParagraphStyle('corr', parent=styles['Heading3'], fontSize=10.5, textColor=colors.HexColor('#002B55'), spaceBefore=8, spaceAfter=3)
    cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8.5, leading=11)

    story = [
        Paragraph(settings.NOM_MINISTERE, h_min),
        Paragraph('République du Niger', h_sub),
        Spacer(1, 6),
        Paragraph(f"<b>Bordereau d'envoi</b> — départs expédiés du {jour:%d/%m/%Y}", styles['Heading2']),
        Spacer(1, 4),
    ]

    # Regroupement par correspondant (destinataire principal).
    groupes = {}
    for c in departs:
        groupes.setdefault(c.correspondant.nom, []).append(c)

    if not groupes:
        story.append(Paragraph('Aucun courrier expédié à cette date.', styles['Normal']))
    else:
        for nom in sorted(groupes):
            story.append(Paragraph(f'Destinataire : {nom}', h_corr))
            data = [['Référence', 'Objet', 'Pièces', 'Signature']]
            for c in groupes[nom]:
                data.append([Paragraph(c.reference_complete or c.numero_ordre, cell),
                             Paragraph(c.objet, cell), str(c.nombre_pieces), ''])
            t = Table(data, colWidths=[45 * mm, 82 * mm, 15 * mm, 32 * mm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004080')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8.5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccd6e0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f6fb')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t)

    doc.build(story)
    return buf.getvalue()


class BordereauView(APIView):
    """GET /api/v1/bordereau/?date=JJ-MM-AAAA — bordereau PDF des départs du jour."""

    def get_permissions(self):
        return [MotDePasseAJour(), AvecPermission('courrier.enregistrer_courrier')()]

    def get(self, request):
        brut = request.query_params.get('date') or ''
        try:
            from datetime import datetime
            jour = datetime.strptime(brut, '%d-%m-%Y').date()
        except ValueError:
            return Response({'detail': 'Date invalide (format attendu : JJ-MM-AAAA).'}, status=400)
        departs = (Courrier.objects.filter(sens='DEPART', expedie_le=jour)
                   .select_related('correspondant', 'structure_emettrice')
                   .order_by('correspondant__nom', 'numero_ordre'))
        pdf = _bordereau_pdf(jour, departs)
        resp = HttpResponse(pdf, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="bordereau-{jour:%Y-%m-%d}.pdf"'
        resp.xframe_options_exempt = True
        resp['Content-Security-Policy'] = f'frame-ancestors {settings.INTRANET_URL}'
        return resp
