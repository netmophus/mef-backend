from django.urls import path

from .views import (
    MinistreView, BiographieView, CabinetListView, DiscoursListView, AlbumListView,
    EvenementListView, DenominationListView, MinistresHistoriqueListView,
    DeleguesHistoriqueListView, TexteOrganisationListView,
)

urlpatterns = [
    path('ministre/', MinistreView.as_view(), name='ministre'),
    path('ministre/biographie/', BiographieView.as_view(), name='ministre-biographie'),
    path('cabinet/', CabinetListView.as_view(), name='cabinet'),
    path('discours/', DiscoursListView.as_view(), name='discours'),
    path('album-ministre/', AlbumListView.as_view(), name='album-ministre'),
    path('evenements/', EvenementListView.as_view(), name='evenements'),
    path('historique/denominations/', DenominationListView.as_view(), name='historique-denominations'),
    path('historique/ministres/', MinistresHistoriqueListView.as_view(), name='historique-ministres'),
    path('historique/ministres-delegues/', DeleguesHistoriqueListView.as_view(), name='historique-delegues'),
    path('historique/textes-organisation/', TexteOrganisationListView.as_view(), name='historique-textes'),
]
