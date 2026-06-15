from django.urls import path
from .views import (
    upload_import_view,
    import_job_detail_view,
    import_anomaly_list_view,
    resolve_anomaly_view,
    execute_import_view,
    import_report_view,
    import_list_view,
)

urlpatterns = [
    path("", import_list_view, name="import-list"),
    path("upload/", upload_import_view, name="import-upload"),
    path("<uuid:job_id>/", import_job_detail_view, name="import-detail"),
    path("<uuid:job_id>/anomalies/", import_anomaly_list_view, name="import-anomaly-list"),
    path("<uuid:job_id>/anomalies/<uuid:anomaly_id>/resolve/", resolve_anomaly_view, name="import-anomaly-resolve"),
    path("<uuid:job_id>/execute/", execute_import_view, name="import-execute"),
    path("<uuid:job_id>/report/", import_report_view, name="import-report"),
]
