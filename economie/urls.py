from django.urls import path

from .views import IndicateursView

urlpatterns = [
    path('indicateurs/', IndicateursView.as_view(), name='indicateurs'),
]
