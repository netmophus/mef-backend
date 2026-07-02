from django.contrib import admin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('titre_court', 'rubrique', 'type', 'ordre', 'actif')
    list_editable = ('type', 'ordre', 'actif')
    list_filter = ('rubrique', 'type', 'actif')
    search_fields = ('titre', 'type')
    ordering = ('rubrique', 'ordre')

    @admin.display(description='Titre')
    def titre_court(self, obj):
        return obj.titre if len(obj.titre) <= 80 else obj.titre[:77] + '…'
