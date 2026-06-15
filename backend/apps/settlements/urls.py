from django.urls import path
from .views import GroupSettlementListCreateView, SettlementDetailView

urlpatterns = [
    path("groups/<uuid:group_id>/", GroupSettlementListCreateView.as_view(), name="group-settlement-list-create"),
    path("<uuid:pk>/", SettlementDetailView.as_view(), name="settlement-detail"),
]
