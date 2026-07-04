from django.contrib import admin

from .models import Registre, CompteurRegistre, Correspondant, Courrier, EvenementCourrier


@admin.register(Registre)
class RegistreAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'sens', 'actif')
    list_filter = ('sens', 'actif')
    search_fields = ('code', 'libelle')


@admin.register(CompteurRegistre)
class CompteurRegistreAdmin(admin.ModelAdmin):
    list_display = ('registre', 'annee', 'dernier_numero')
    list_filter = ('registre', 'annee')

    def has_add_permission(self, request):
        return False


@admin.register(Correspondant)
class CorrespondantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type', 'actif')
    list_filter = ('type', 'actif')
    search_fields = ('nom',)


class EvenementCourrierInline(admin.TabularInline):
    model = EvenementCourrier
    extra = 0
    can_delete = False
    readonly_fields = ('type', 'acteur', 'horodatage', 'details')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Courrier)
class CourrierAdmin(admin.ModelAdmin):
    """Lecture seule (support). La saisie se fait dans l'intranet."""

    list_display = ('numero_ordre', 'date_arrivee', 'correspondant', 'objet',
                    'confidentialite', 'statut')
    list_filter = ('registre', 'statut', 'confidentialite')
    search_fields = ('numero_ordre', 'objet', 'correspondant__nom')
    date_hierarchy = 'date_arrivee'
    inlines = [EvenementCourrierInline]

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
