from django.contrib import admin

from .models import Photo, Video


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre',)
    ordering = ('ordre', 'id')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date', 'duree', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre',)
    ordering = ('ordre', 'id')
