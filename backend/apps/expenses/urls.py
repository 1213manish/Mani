from django.urls import path
from .views import GroupExpenseListCreateView, ExpenseDetailView

urlpatterns = [
    path("groups/<uuid:group_id>/", GroupExpenseListCreateView.as_view(), name="group-expense-list-create"),
    path("<uuid:pk>/", ExpenseDetailView.as_view(), name="expense-detail"),
]
