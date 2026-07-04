from django.urls import path

from .views import (
    LoginView, RefreshView, LogoutView, MeView, ChangerMotDePasseView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('changer-mot-de-passe/', ChangerMotDePasseView.as_view(), name='auth-changer-mdp'),
]
