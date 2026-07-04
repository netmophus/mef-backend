from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer, ChangerMotDePasseSerializer, payload_utilisateur,
)

User = get_user_model()


def _set_jwt_cookies(response, access, refresh):
    """Pose les deux cookies httpOnly (access sur /, refresh sur /api/v1/auth/).

    Le cookie `mef_access` vit aussi longtemps que le refresh (12 h) alors que
    le JWT qu'il contient n'est valable que 15 min : ainsi, après expiration du
    JWT, le cookie est toujours présent → le proxy laisse passer, /me/ renvoie
    401 et lib/api.js déclenche un refresh silencieux (pas de retour au login).
    """
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE, str(access),
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        httponly=True, secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE, path='/',
    )
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE, str(refresh),
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        httponly=True, secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE, path=settings.JWT_REFRESH_COOKIE_PATH,
    )


def _delete_jwt_cookies(response):
    response.delete_cookie(settings.JWT_ACCESS_COOKIE, path='/')
    response.delete_cookie(settings.JWT_REFRESH_COOKIE, path=settings.JWT_REFRESH_COOKIE_PATH)


IDENTIFIANTS_INVALIDES = 'Matricule ou mot de passe incorrect'


class LoginView(APIView):
    """POST /api/v1/auth/login/ — { matricule, mot_de_passe }."""

    permission_classes = [AllowAny]
    authentication_classes = []  # ne pas exiger de jeton préalable

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        # authenticate() renvoie None si identifiants faux OU compte inactif.
        user = authenticate(
            request,
            username=ser.validated_data['matricule'],
            password=ser.validated_data['mot_de_passe'],
        )
        if user is None:
            return Response({'detail': IDENTIFIANTS_INVALIDES}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        resp = Response({
            'utilisateur': payload_utilisateur(user),
            'doit_changer_mdp': user.doit_changer_mdp,
        })
        _set_jwt_cookies(resp, refresh.access_token, refresh)
        return resp


class RefreshView(APIView):
    """POST /api/v1/auth/refresh/ — rotation depuis le cookie mef_refresh."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def _echec(self, detail):
        # Session morte : on renvoie 401 ET on purge les cookies pour éviter
        # une boucle de redirection /login ↔ / (cookie périmé jamais nettoyé).
        resp = Response({'detail': detail}, status=status.HTTP_401_UNAUTHORIZED)
        _delete_jwt_cookies(resp)
        return resp

    def post(self, request):
        raw = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if not raw:
            return self._echec('Session absente.')
        try:
            old = RefreshToken(raw)
        except TokenError:
            return self._echec('Session expirée.')

        try:
            user = User.objects.get(pk=old['user_id'])
        except (User.DoesNotExist, KeyError):
            return self._echec('Session invalide.')
        if not user.is_active:
            return self._echec('Compte désactivé.')

        # Rotation : on blackliste l'ancien refresh puis on en émet un nouveau.
        try:
            old.blacklist()
        except AttributeError:
            pass
        new_refresh = RefreshToken.for_user(user)
        resp = Response({'detail': 'ok'})
        _set_jwt_cookies(resp, new_refresh.access_token, new_refresh)
        return resp


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blackliste le refresh et supprime les cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        resp = Response(status=status.HTTP_204_NO_CONTENT)
        _delete_jwt_cookies(resp)
        return resp


class MeView(APIView):
    """GET /api/v1/auth/me/ — infos de l'utilisateur connecté."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'utilisateur': payload_utilisateur(user),
            'doit_changer_mdp': user.doit_changer_mdp,
            'nom_ministere': settings.NOM_MINISTERE,
        })


class ConfigView(APIView):
    """GET /api/v1/config/ — configuration publique (avant authentification)."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'nom_ministere': settings.NOM_MINISTERE})


class ChangerMotDePasseView(APIView):
    """POST /api/v1/auth/changer-mot-de-passe/ — accessible même si doit_changer_mdp=True."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ChangerMotDePasseSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({'detail': 'Mot de passe modifié avec succès.'})
