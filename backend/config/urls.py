"""
URL configuration for ExpenseFlow backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),

    # API v1
    path("api/auth/", include("apps.accounts.urls")),
    path("api/groups/", include("apps.groups.urls")),
    path("api/expenses/", include("apps.expenses.urls")),
    path("api/settlements/", include("apps.settlements.urls")),
    path("api/balances/", include("apps.balances.urls")),
    path("api/imports/", include("apps.imports.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/ai/", include("apps.ai_assist.urls")),
    path("api/currencies/", include("apps.currencies.urls")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
