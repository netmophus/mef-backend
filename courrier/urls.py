from rest_framework.routers import DefaultRouter

from .views import CourrierViewSet, CorrespondantViewSet

router = DefaultRouter()
# Enregistré AVANT 'courriers' pour que /courriers/correspondants/ ne soit pas
# capturé comme un détail de courrier (pk='correspondants').
router.register('courriers/correspondants', CorrespondantViewSet, basename='correspondant')
router.register('courriers', CourrierViewSet, basename='courrier')

urlpatterns = router.urls
