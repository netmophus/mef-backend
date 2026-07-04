from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CourrierViewSet, CorrespondantViewSet, ImputationViewSet, BannetteView, DirectionListView,
    TableauBordView,
)

router = DefaultRouter()
router.register('courriers/correspondants', CorrespondantViewSet, basename='correspondant')
router.register('courriers', CourrierViewSet, basename='courrier')
router.register('imputations', ImputationViewSet, basename='imputation')

urlpatterns = [
    path('bannette/', BannetteView.as_view(), name='bannette'),
    path('tableau-bord/', TableauBordView.as_view(), name='tableau-bord'),
    path('directions/', DirectionListView.as_view(), name='directions'),
    *router.urls,
]
