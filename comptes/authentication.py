from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authentifie via le cookie httpOnly `mef_access`.

    Repli sur l'en-tête `Authorization: Bearer ...` (pratique pour les tests
    Postman/curl). Renvoie None si aucun jeton n'est présent (endpoint alors
    traité selon ses permissions).
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE)

        if raw_token is None:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
