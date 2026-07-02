from django.urls import path

from .views import ActualiteListView, RevueAnneesView, RevueNumerosView

urlpatterns = [
    path('actualites/', ActualiteListView.as_view(), name='actualites'),
    path('revue-presse/annees/', RevueAnneesView.as_view(), name='revue-annees'),
    path('revue-presse/<int:annee>/', RevueNumerosView.as_view(), name='revue-numeros'),
]
