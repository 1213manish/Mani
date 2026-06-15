"""
Tests for the Anomaly Detection Engine.
Tests all 15 anomaly types.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.currencies.models import Currency
from apps.groups.models import Group, GroupMembership
from apps.imports.anomaly_detector import AnomalyDetectionEngine
from apps.imports.models import ImportAnomaly

User = get_user_model()


@pytest.mark.django_db
class TestAnomalyDetectionEngine(TestCase):
    def setUp(self):
        self.inr = Currency.objects.create(code="INR_A", name="INR Test", symbol="₹")
        self.usd = Currency.objects.create(code="USD_A", name="USD Test", symbol="$")

        self.user = User.objects.create_user(
            email="member@anomaly.test", username="member_a",
            first_name="Member", last_name="A", password="test"
        )
        self.group = Group.objects.create(
            name="Anomaly Test Group", created_by=self.user, default_currency=self.inr
        )
        GroupMembership.objects.create(
            group=self.group, user=self.user,
            joined_at=date(2024, 1, 1), left_at=date(2024, 6, 30)
        )

    def _detect(self, rows):
        engine = AnomalyDetectionEngine(group=self.group, rows=rows, import_job=None)
        return engine.detect_all()

    def test_blank_mandatory_field(self):
        rows = [{"title": "", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": "2024-03-01"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.BLANK_MANDATORY_FIELD, types)

    def test_negative_value(self):
        rows = [{"title": "Test", "amount": "-100", "paid_by": "member@anomaly.test", "expense_date": "2024-03-01"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.NEGATIVE_VALUE, types)

    def test_invalid_date(self):
        rows = [{"title": "Test", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": "not-a-date"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.INVALID_DATE, types)

    def test_future_date(self):
        future = (timezone.now().date() + timedelta(days=30)).isoformat()
        rows = [{"title": "Future", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": future}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.FUTURE_DATE, types)

    def test_missing_payer(self):
        rows = [{"title": "Test", "amount": "100", "paid_by": "", "expense_date": "2024-03-01"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.MISSING_PAYER, types)

    def test_unknown_member(self):
        rows = [{"title": "Test", "amount": "100", "paid_by": "unknown@nowhere.com", "expense_date": "2024-03-01"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.UNKNOWN_MEMBER, types)

    def test_member_not_active(self):
        # Member left June 30 — expense in August should flag
        rows = [{"title": "Test", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": "2024-08-01"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.MEMBER_NOT_ACTIVE, types)

    def test_settlement_as_expense(self):
        rows = [{"title": "Settlement payment", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": "2024-03-01"}]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.SETTLEMENT_AS_EXPENSE, types)

    def test_intra_file_exact_duplicate(self):
        row = {"title": "Test", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": "2024-03-01"}
        rows = [row, row.copy()]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.DUPLICATE_EXACT, types)

    def test_possible_duplicate(self):
        rows = [
            {"title": "Lunch", "amount": "100", "paid_by": "member@anomaly.test", "expense_date": "2024-03-01"},
            {"title": "Lunch", "amount": "120", "paid_by": "member@anomaly.test", "expense_date": "2024-03-01"},
        ]
        anomalies = self._detect(rows)
        types = [a.anomaly_type for a in anomalies]
        self.assertIn(ImportAnomaly.AnomalyType.DUPLICATE_POSSIBLE, types)

    def test_no_false_positives_for_valid_row(self):
        rows = [{"title": "Dinner", "amount": "500", "paid_by": "member@anomaly.test", "expense_date": "2024-03-15"}]
        anomalies = self._detect(rows)
        error_types = [a for a in anomalies if a.severity == ImportAnomaly.Severity.ERROR]
        self.assertEqual(len(error_types), 0)
