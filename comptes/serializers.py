from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


def payload_utilisateur(user):
    """Infos utilisateur renvoyées par /login/ et /me/ (dont rôles + permissions)."""
    direction = None
    if user.direction_id:
        direction = {'id': user.direction.id, 'sigle': user.direction.sigle, 'nom': user.direction.nom}
    return {
        'matricule': user.matricule,
        'nom_complet': user.get_full_name() or user.matricule,
        'email': user.email,
        'direction': direction,
        'fonction': user.fonction,
        # RBAC : groups (rôles) + permissions effectives au format « app.codename ».
        'roles': list(user.groups.values_list('name', flat=True)),
        'permissions': sorted(user.get_all_permissions()),
    }


class LoginSerializer(serializers.Serializer):
    matricule = serializers.CharField()
    mot_de_passe = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)


class ChangerMotDePasseSerializer(serializers.Serializer):
    mot_de_passe_actuel = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    nouveau_mot_de_passe = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    confirmation = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate_mot_de_passe_actuel(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Le mot de passe actuel est incorrect.')
        return value

    def validate(self, attrs):
        if attrs['nouveau_mot_de_passe'] != attrs['confirmation']:
            raise serializers.ValidationError(
                {'confirmation': 'La confirmation ne correspond pas au nouveau mot de passe.'})
        user = self.context['request'].user
        validate_password(attrs['nouveau_mot_de_passe'], user)
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['nouveau_mot_de_passe'])
        user.doit_changer_mdp = False
        user.save(update_fields=['password', 'doit_changer_mdp'])
        return user
