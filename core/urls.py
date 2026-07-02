from django.urls import path

from .views import HeaderView, LiensPartenairesView

urlpatterns = [
    path('header/', HeaderView.as_view(), name='header'),
    path('liens-partenaires/', LiensPartenairesView.as_view(), name='liens-partenaires'),
]
