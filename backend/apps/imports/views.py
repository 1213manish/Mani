"""
Imports views: Upload CSV, detect anomalies, approve/reject, execute import.
"""

import hashlib
import os
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from apps.groups.models import Group
from .anomaly_detector import AnomalyDetectionEngine
from .csv_parser import parse_csv
from .models import ImportJob, ImportAnomaly
from .report_generator import generate_import_report
from .serializers import (
    ImportJobSerializer,
    ImportAnomalySerializer,
    ImportUploadSerializer,
    AnomalyResolveSerializer,
)


def get_member_group_or_404(user, group_id):
    return get_object_or_404(
        Group, id=group_id,
        memberships__user=user, memberships__left_at__isnull=True, is_active=True,
    )


@extend_schema(tags=["Imports"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_import_view(request):
    """
    Upload a CSV file for import.
    Steps:
    1. Parse file
    2. Detect all anomalies
    3. Save ImportJob + ImportAnomalies
    4. Return job with anomaly list (status = AWAITING_APPROVAL)
    """
    serializer = ImportUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    group = get_member_group_or_404(request.user, serializer.validated_data["group_id"])
    uploaded_file = serializer.validated_data["file"]

    # Read file
    file_content = uploaded_file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()

    # Check for duplicate import (same file already imported in this group)
    if ImportJob.objects.filter(group=group, file_hash=file_hash, status=ImportJob.Status.COMPLETED).exists():
        return Response(
            {
                "error": "This exact file has already been successfully imported into this group.",
                "code": "DUPLICATE_FILE",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save file to disk
    media_dir = os.path.join(settings.MEDIA_ROOT, "imports", str(group.id))
    os.makedirs(media_dir, exist_ok=True)
    file_path = os.path.join(media_dir, f"{file_hash[:8]}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Create ImportJob
    import_job = ImportJob.objects.create(
        group=group,
        uploaded_by=request.user,
        file_name=uploaded_file.name,
        file_path=file_path,
        file_hash=file_hash,
        status=ImportJob.Status.PARSING,
    )

    try:
        # Parse CSV
        rows, parse_warnings = parse_csv(file_content)
        import_job.rows_total = len(rows)
        import_job.status = ImportJob.Status.PARSING
        import_job.save(update_fields=["rows_total", "status"])

        # Run anomaly detection
        engine = AnomalyDetectionEngine(group=group, rows=rows, import_job=import_job)
        anomaly_instances = engine.detect_all()

        # Save anomalies
        ImportAnomaly.objects.bulk_create(anomaly_instances, batch_size=100)
        import_job.anomalies_count = len(anomaly_instances)
        import_job.status = ImportJob.Status.AWAITING_APPROVAL
        import_job.save(update_fields=["anomalies_count", "status"])

    except Exception as e:
        import_job.status = ImportJob.Status.FAILED
        import_job.error_message = str(e)
        import_job.save(update_fields=["status", "error_message"])
        return Response(
            {"error": f"Import parsing failed: {str(e)}", "code": "PARSE_ERROR"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        ImportJobSerializer(import_job).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=["Imports"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def import_job_detail_view(request, job_id):
    """Get status and details of an import job."""
    import_job = get_object_or_404(
        ImportJob, id=job_id, group__memberships__user=request.user,
        group__memberships__left_at__isnull=True,
    )
    return Response(ImportJobSerializer(import_job).data)


@extend_schema(tags=["Imports"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def import_anomaly_list_view(request, job_id):
    """List all anomalies for an import job."""
    import_job = get_object_or_404(
        ImportJob, id=job_id, group__memberships__user=request.user,
        group__memberships__left_at__isnull=True,
    )
    anomalies = import_job.anomalies.all()

    # Filter by severity or status
    severity = request.query_params.get("severity")
    status_filter = request.query_params.get("status")
    if severity:
        anomalies = anomalies.filter(severity=severity.upper())
    if status_filter:
        anomalies = anomalies.filter(status=status_filter.upper())

    return Response(ImportAnomalySerializer(anomalies, many=True).data)


@extend_schema(tags=["Imports"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_anomaly_view(request, job_id, anomaly_id):
    """
    Approve or reject a single anomaly.
    User approval required — system never auto-modifies data.
    """
    import_job = get_object_or_404(
        ImportJob, id=job_id, group__memberships__user=request.user,
        group__memberships__left_at__isnull=True,
    )
    anomaly = get_object_or_404(ImportAnomaly, id=anomaly_id, import_job=import_job)

    serializer = AnomalyResolveSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    action = serializer.validated_data["action"]
    if action == "APPROVE":
        anomaly.status = ImportAnomaly.AnomalyStatus.APPROVED
        anomaly.action_taken = serializer.validated_data.get("action_taken", "User approved import of this row.")
    else:
        anomaly.status = ImportAnomaly.AnomalyStatus.REJECTED
        anomaly.action_taken = serializer.validated_data.get("action_taken", "User rejected this row.")

    anomaly.resolved_by = request.user
    anomaly.resolved_at = timezone.now()
    anomaly.save()

    return Response(ImportAnomalySerializer(anomaly).data)


@extend_schema(tags=["Imports"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def execute_import_view(request, job_id):
    """
    Execute the import: only import rows that have no ERROR anomalies,
    or where ERROR anomalies have been explicitly approved.
    """
    import_job = get_object_or_404(
        ImportJob, id=job_id, group__memberships__user=request.user,
        group__memberships__left_at__isnull=True,
    )

    if import_job.status not in [ImportJob.Status.AWAITING_APPROVAL, ImportJob.Status.APPROVED]:
        return Response(
            {"error": f"Cannot execute import in '{import_job.status}' status."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check for unresolved ERROR anomalies
    pending_errors = import_job.anomalies.filter(
        severity=ImportAnomaly.Severity.ERROR,
        status=ImportAnomaly.AnomalyStatus.PENDING,
    ).count()

    if pending_errors > 0:
        return Response(
            {
                "error": f"There are {pending_errors} unresolved ERROR anomalies. Please review all errors before executing.",
                "code": "PENDING_ERRORS",
                "pending_errors": pending_errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Re-read and parse the file
    try:
        with open(import_job.file_path, "rb") as f:
            file_content = f.read()
        rows, _ = parse_csv(file_content)
    except Exception as e:
        import_job.status = ImportJob.Status.FAILED
        import_job.error_message = f"Could not read import file: {str(e)}"
        import_job.save(update_fields=["status", "error_message"])
        return Response({"error": import_job.error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Determine which rows to skip
    rejected_rows = set(
        import_job.anomalies.filter(
            status=ImportAnomaly.AnomalyStatus.REJECTED
        ).values_list("row_number", flat=True)
    )
    error_rejected_rows = set(
        import_job.anomalies.filter(
            severity=ImportAnomaly.Severity.ERROR,
            status__in=[ImportAnomaly.AnomalyStatus.PENDING],
        ).values_list("row_number", flat=True)
    )
    skip_rows = rejected_rows | error_rejected_rows

    # Import approved rows
    from django.contrib.auth import get_user_model
    from apps.currencies.models import Currency
    from apps.expenses.models import Expense, ExpenseSplit
    from apps.expenses.serializers import ExpenseCreateSerializer

    User = get_user_model()
    imported = 0
    skipped = 0

    for i, row in enumerate(rows):
        row_num = i + 1
        if row_num in skip_rows:
            skipped += 1
            continue

        try:
            # Resolve payer (email, username, or first_name)
            payer_ref = str(row.get("paid_by", "")).strip().lower()
            payer = None
            for membership in import_job.group.memberships.all().select_related("user"):
                user = membership.user
                if (user.email.lower() == payer_ref or 
                    user.username.lower() == payer_ref or 
                    user.first_name.lower() == payer_ref):
                    payer = user
                    break
            
            if not payer:
                try:
                    if "@" in payer_ref:
                        payer = User.objects.get(email=payer_ref)
                    else:
                        payer = User.objects.get(username__iexact=payer_ref)
                except User.DoesNotExist:
                    skipped += 1
                    continue

            # Parse date
            from apps.imports.csv_parser import parse_csv as _
            from datetime import datetime as _dt
            date_str = str(row.get("expense_date", "")).strip()
            expense_date = None
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    expense_date = _dt.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            if not expense_date:
                skipped += 1
                continue

            # Resolve currency
            currency_code = str(row.get("currency", import_job.group.default_currency.code if import_job.group.default_currency else "INR")).strip().upper()
            try:
                currency = Currency.objects.get(code=currency_code)
            except Currency.DoesNotExist:
                currency = Currency.objects.get(code="INR")

            amount = Decimal(str(row.get("amount", "0")).replace(",", ""))
            if amount <= 0:
                skipped += 1
                continue

            expense = Expense.objects.create(
                title=str(row.get("title", "")).strip(),
                description=str(row.get("description", "")).strip(),
                amount=amount,
                currency=currency,
                original_amount=amount,
                original_currency=currency,
                exchange_rate=Decimal("1.0"),
                converted_amount=amount,
                paid_by=payer,
                expense_date=expense_date,
                group=import_job.group,
                split_type=str(row.get("split_type", "EQUAL")).strip().upper(),
                notes=str(row.get("notes", "")).strip(),
                category=str(row.get("category", "")).strip(),
                created_by=import_job.uploaded_by,
                import_job=import_job,
            )

            # Create equal splits for active members
            active_members = list(import_job.group.get_active_members(expense_date))
            if active_members:
                per_person = (amount / len(active_members)).quantize(Decimal("0.0001"))
                from decimal import ROUND_HALF_UP
                splits = []
                for j, member in enumerate(active_members):
                    member_amount = per_person
                    if j == 0:
                        member_amount += amount - (per_person * len(active_members))
                    splits.append(
                        ExpenseSplit(expense=expense, user=member, owed_amount=member_amount, share_amount=member_amount)
                    )
                ExpenseSplit.objects.bulk_create(splits)

            imported += 1

        except Exception:
            skipped += 1
            continue

    # Generate report
    import_job.rows_imported = imported
    import_job.rows_skipped = skipped
    import_job.status = ImportJob.Status.COMPLETED
    import_job.completed_at = timezone.now()
    import_job.save()

    # Generate and save report
    report_content = generate_import_report(import_job)
    report_dir = os.path.join(settings.MEDIA_ROOT, "import_reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"report_{import_job.id}.csv")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(report_content)
    import_job.report_path = report_path
    import_job.save(update_fields=["report_path"])

    return Response(ImportJobSerializer(import_job).data)


@extend_schema(tags=["Imports"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def import_report_view(request, job_id):
    """Download the import report as CSV."""
    import_job = get_object_or_404(
        ImportJob, id=job_id, group__memberships__user=request.user,
        group__memberships__left_at__isnull=True,
    )

    if not import_job.report_path or not os.path.exists(import_job.report_path):
        # Generate on-the-fly
        report_content = generate_import_report(import_job)
    else:
        with open(import_job.report_path, "r", encoding="utf-8") as f:
            report_content = f.read()

    response = HttpResponse(report_content, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="import_report_{import_job.id}.csv"'
    return response


@extend_schema(tags=["Imports"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def import_list_view(request):
    """List all import jobs for groups the user belongs to."""
    jobs = ImportJob.objects.filter(
        group__memberships__user=request.user,
        group__memberships__left_at__isnull=True,
    ).select_related("uploaded_by", "group").distinct().order_by("-created_at")

    group_id = request.query_params.get("group_id")
    if group_id:
        jobs = jobs.filter(group_id=group_id)

    return Response(ImportJobSerializer(jobs, many=True).data)
