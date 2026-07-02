from django.contrib import admin

from .models import IndicateurMacro, IndicateurCle


@admin.register(IndicateurMacro)
class IndicateurMacroAdmin(admin.ModelAdmin):
    list_display = ('label', 'valeur', 'suffixe', 'unite', 'icone', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('label',)
    ordering = ('ordre', 'id')


@admin.register(IndicateurCle)
class IndicateurCleAdmin(admin.ModelAdmin):
    list_display = ('label', 'valeur', 'maximum', 'note', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('label',)
    ordering = ('ordre', 'id')
