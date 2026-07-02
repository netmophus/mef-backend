from django.contrib import admin

from .models import SiteConfig, MenuItem, LienUtile, Partenaire, BlocReforme


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Identité', {'fields': ('nom', 'sous_titre', 'logo')}),
        ('Coordonnées', {'fields': ('telephone', 'email', 'adresse')}),
        ('Réseaux sociaux', {'fields': ('facebook', 'twitter', 'youtube')}),
    )

    # Singleton : une seule ligne, non supprimable.
    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('label', 'parent', 'path', 'ordre', 'visible')
    list_editable = ('ordre', 'visible')
    list_filter = ('visible', 'parent')
    search_fields = ('label', 'path')
    ordering = ('ordre', 'id')


@admin.register(LienUtile)
class LienUtileAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'ordre', 'actif')
    list_editable = ('url', 'ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('label',)
    ordering = ('ordre', 'id')


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'sigle', 'initiales', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('nom', 'sigle')
    ordering = ('ordre', 'id')


@admin.register(BlocReforme)
class BlocReformeAdmin(admin.ModelAdmin):
    # Singleton : une seule fiche, non supprimable.
    def has_add_permission(self, request):
        return not BlocReforme.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
