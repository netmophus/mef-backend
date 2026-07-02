from django.urls import path

from .views import SlideListView, QuickLinkListView

urlpatterns = [
    path('slides/', SlideListView.as_view(), name='slides'),
    path('quick-links/', QuickLinkListView.as_view(), name='quick-links'),
]
