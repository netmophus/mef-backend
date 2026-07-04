from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Direction, Utilisateur


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('sigle', 'nom', 'parent', 'ordre')
    list_editable = ('ordre',)
    list_filter = ('parent',)
    search_fields = ('sigle', 'nom')
    autocomplete_fields = ('parent',)
    ordering = ('ordre', 'sigle')


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    ordering = ('matricule',)
    list_display = ('matricule', 'nom_complet', 'direction', 'fonction',
                    'is_active', 'doit_changer_mdp', 'last_login')
    list_filter = ('direction', 'is_active', 'doit_changer_mdp', 'is_staff', 'is_superuser')
    search_fields = ('matricule', 'first_name', 'last_name', 'email')
    autocomplete_fields = ('direction', 'superieur')
    filter_horizontal = ('groups', 'user_permissions')  # affectation ergonomique aux groupes
    actions = ['reinitialiser_changement_mdp']

    fieldsets = (
        (None, {'fields': ('matricule', 'password')}),
        ('Identité', {'fields': ('first_name', 'last_name', 'email')}),
        ('Affectation', {'fields': ('direction', 'fonction', 'superieur', 'telephone', 'bureau')}),
        ('Sécurité intranet', {'fields': ('doit_changer_mdp',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('matricule', 'first_name', 'last_name', 'email',
                       'direction', 'fonction', 'password1', 'password2'),
        }),
    )

    @admin.display(description='Nom complet')
    def nom_complet(self, obj):
        return obj.get_full_name()

    @admin.action(description="Réinitialiser l'obligation de changement de mot de passe")
    def reinitialiser_changement_mdp(self, request, queryset):
        n = queryset.update(doit_changer_mdp=True)
        self.message_user(request, f"{n} compte(s) devront changer leur mot de passe à la prochaine connexion.")
