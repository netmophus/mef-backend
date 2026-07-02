from django.contrib import admin

from .models import Actualite, NumeroRevue


@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'rubrique', 'date', 'a_la_une', 'actif')
    list_editable = ('rubrique', 'a_la_une', 'actif')
    list_filter = ('rubrique', 'a_la_une', 'actif')
    search_fields = ('titre', 'chapo', 'contenu')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(NumeroRevue)
class NumeroRevueAdmin(admin.ModelAdmin):
    list_display = ('titre', 'annee', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('annee', 'actif')
    search_fields = ('titre',)
    ordering = ('-annee', 'ordre')
