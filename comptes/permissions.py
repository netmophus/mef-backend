from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class MotDePasseAJour(BasePermission):
    """Refuse l'accès tant que l'utilisateur doit changer son mot de passe.

    À appliquer sur les futurs endpoints intranet (PAS sur /me/, /logout/ ni
    /changer-mot-de-passe/). Renvoie un 403 avec le code CHANGEMENT_MDP_REQUIS.
    """

    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated and getattr(user, 'doit_changer_mdp', False):
            raise PermissionDenied({
                'code': 'CHANGEMENT_MDP_REQUIS',
                'detail': 'Vous devez changer votre mot de passe avant de continuer.',
            })
        return True


def AvecPermission(codename):
    """Fabrique une permission DRF qui exige `user.has_perm(codename)`.

    Usage : permission_classes = [MotDePasseAJour, AvecPermission('courrier.enregistrer_courrier')]
    `codename` est au format « app_label.codename ».
    """

    class _AvecPermission(BasePermission):
        message = "Vous n'avez pas l'autorisation d'effectuer cette action."

        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.has_perm(codename))

    return _AvecPermission
