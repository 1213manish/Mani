from django.urls import path
from .views import explain_balance_ai_view, explain_anomaly_ai_view, suggest_resolution_ai_view

urlpatterns = [
    path("explain-balance/", explain_balance_ai_view, name="ai-explain-balance"),
    path("explain-anomaly/", explain_anomaly_ai_view, name="ai-explain-anomaly"),
    path("suggest-resolution/", suggest_resolution_ai_view, name="ai-suggest-resolution"),
]
