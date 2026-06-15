from django.urls import path
from .views import group_balances_view, simplified_settlements_view, explain_balance_view

urlpatterns = [
    path("groups/<uuid:group_id>/", group_balances_view, name="group-balances"),
    path("groups/<uuid:group_id>/simplified/", simplified_settlements_view, name="group-balances-simplified"),
    path("groups/<uuid:group_id>/explain/", explain_balance_view, name="group-balances-explain"),
]
