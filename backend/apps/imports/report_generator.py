"""
Import report generator.

Generates a downloadable import report after a job completes.
"""

import csv
import io
from datetime import datetime

from .models import ImportJob, ImportAnomaly


def generate_import_report(import_job: ImportJob) -> str:
    """
    Generate a CSV report of the import job results.

    Returns the report as a string (to be saved to file/served as download).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header section
    writer.writerow(["EXPENSEFLOW IMPORT REPORT"])
    writer.writerow(["Generated at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")])
    writer.writerow(["Import Job ID", str(import_job.id)])
    writer.writerow(["File Name", import_job.file_name])
    writer.writerow(["Uploaded By", import_job.uploaded_by.email])
    writer.writerow(["Group", import_job.group.name])
    writer.writerow(["Status", import_job.status])
    writer.writerow([])

    # Summary section
    writer.writerow(["=== SUMMARY ==="])
    writer.writerow(["Rows Processed", import_job.rows_total])
    writer.writerow(["Rows Imported", import_job.rows_imported])
    writer.writerow(["Rows Skipped", import_job.rows_skipped])
    writer.writerow(["Anomalies Found", import_job.anomalies_count])
    writer.writerow([])

    # Anomaly detail section
    anomalies = ImportAnomaly.objects.filter(import_job=import_job).order_by("row_number")

    if anomalies.exists():
        writer.writerow(["=== ANOMALY DETAILS ==="])
        writer.writerow([
            "Row #", "Anomaly Type", "Severity", "Status",
            "Description", "Recommendation", "Action Taken",
            "Resolved By", "Resolved At",
        ])
        for anomaly in anomalies:
            writer.writerow([
                anomaly.row_number,
                anomaly.anomaly_type,
                anomaly.severity,
                anomaly.status,
                anomaly.description,
                anomaly.recommendation,
                anomaly.action_taken or "",
                anomaly.resolved_by.email if anomaly.resolved_by else "",
                anomaly.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if anomaly.resolved_at else "",
            ])
    else:
        writer.writerow(["No anomalies detected."])

    return output.getvalue()
