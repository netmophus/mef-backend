from django.urls import path

from .views import PhotoListView, VideoListView

urlpatterns = [
    path('mediatheque/photos/', PhotoListView.as_view(), name='mediatheque-photos'),
    path('mediatheque/videos/', VideoListView.as_view(), name='mediatheque-videos'),
]
