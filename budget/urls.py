from django.urls import path

from .views import BudgetAnneesView, BudgetDocumentsView

urlpatterns = [
    path('budget/<slug:rubrique>/annees/', BudgetAnneesView.as_view(), name='budget-annees'),
    path('budget/<slug:rubrique>/<int:annee>/', BudgetDocumentsView.as_view(), name='budget-documents'),
]
