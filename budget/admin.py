from django.contrib import admin

from .models import DocumentBudget


@admin.register(DocumentBudget)
class DocumentBudgetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'rubrique', 'annee', 'type', 'ordre', 'actif')
    list_editable = ('annee', 'type', 'ordre', 'actif')
    list_filter = ('rubrique', 'actif', 'annee')
    search_fields = ('titre', 'type')
    ordering = ('rubrique', '-annee', 'ordre')
