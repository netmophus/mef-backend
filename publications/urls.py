from django.urls import path

from .views import PublicationListView

urlpatterns = [
    path('publications/<slug:rubrique>/', PublicationListView.as_view(), name='publications'),
]
