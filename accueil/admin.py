from django.contrib import admin

from .models import Slide, QuickLink


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre', 'categorie', 'texte')
    ordering = ('ordre', 'id')
    fieldsets = (
        ('Contenu', {'fields': ('categorie', 'titre', 'texte')}),
        ('Visuel', {'fields': ('image', 'secours', 'position')}),
        ('Bouton principal', {'fields': ('cta_label', 'cta_href', 'cta_icon')}),
        ('Bouton secondaire (optionnel)', {'fields': ('cta2_label', 'cta2_href')}),
        ('Affichage', {'fields': ('ordre', 'actif')}),
    )


@admin.register(QuickLink)
class QuickLinkAdmin(admin.ModelAdmin):
    list_display = ('nom', 'icone', 'href', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('nom', 'href')
    ordering = ('ordre', 'id')
    fieldsets = (
        ('Contenu', {'fields': ('nom', 'icone', 'href')}),
        ('Couleurs (dégradé)', {'fields': ('couleur_debut', 'couleur_fin')}),
        ('Affichage', {'fields': ('ordre', 'actif')}),
    )
