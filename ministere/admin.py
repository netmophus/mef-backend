from django.contrib import admin

from .models import (
    Ministre, MinistreLien, MinistreRepere, MinistreParcours,
    MembreCabinet, Discours, AlbumPhoto, Evenement,
    Denomination, MinistreHistorique, TexteOrganisation,
)


class MinistreRepereInline(admin.TabularInline):
    model = MinistreRepere
    extra = 0


class MinistreParcoursInline(admin.TabularInline):
    model = MinistreParcours
    extra = 0


@admin.register(Ministre)
class MinistreAdmin(admin.ModelAdmin):
    inlines = [MinistreRepereInline, MinistreParcoursInline]
    fieldsets = (
        ('Carte (accueil)', {'fields': ('nom', 'fonction', 'photo', 'etiquette')}),
        ('Biographie — identité', {'fields': ('nom_complet',)}),
        ('Biographie — présentation', {'fields': ('presentation_accroche', 'presentation_corps')}),
        ('Biographie — expérience', {'fields': ('experience',)}),
        ("Biographie — conseils d'administration", {'fields': ('conseils_periode', 'conseils')}),
    )

    # Singleton : une seule fiche, non supprimable.
    def has_add_permission(self, request):
        return not Ministre.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MinistreLien)
class MinistreLienAdmin(admin.ModelAdmin):
    list_display = ('label', 'icone', 'href', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('label', 'href')
    ordering = ('ordre', 'id')


@admin.register(MembreCabinet)
class MembreCabinetAdmin(admin.ModelAdmin):
    list_display = ('nom', 'fonction', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('nom', 'fonction')
    ordering = ('ordre', 'id')


@admin.register(Discours)
class DiscoursAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre', 'extrait')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(AlbumPhoto)
class AlbumPhotoAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'date', 'ordre', 'actif')
    list_editable = ('categorie', 'ordre', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('titre',)
    ordering = ('ordre', 'id')


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'date_debut', 'lieu', 'a_la_une', 'actif')
    list_editable = ('type', 'a_la_une', 'actif')
    list_filter = ('type', 'a_la_une', 'actif')
    search_fields = ('titre', 'lieu', 'description')
    date_hierarchy = 'date_debut'
    ordering = ('-date_debut',)


@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ('an', 'nom', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('an', 'nom')
    ordering = ('ordre', 'id')


@admin.register(MinistreHistorique)
class MinistreHistoriqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'description', 'ordre', 'actif')
    list_editable = ('categorie', 'ordre', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('nom', 'description')
    ordering = ('categorie', 'ordre')


@admin.register(TexteOrganisation)
class TexteOrganisationAdmin(admin.ModelAdmin):
    list_display = ('apercu', 'annee', 'ordre', 'actif')
    list_editable = ('annee', 'ordre', 'actif')
    list_filter = ('annee', 'actif')
    search_fields = ('titre',)
    ordering = ('ordre', 'id')

    @admin.display(description='Titre')
    def apercu(self, obj):
        return obj.titre if len(obj.titre) <= 80 else obj.titre[:77] + '…'
