"""
Anomaly Detection Engine.

Implements all 15 anomaly checks for CSV imports.
Each check is a self-contained method returning a list of ImportAnomaly instances.

DESIGN PRINCIPLES:
- Checks are independent — a row can have multiple anomalies.
- No data is modified during detection.
- Severity: ERROR blocks import, WARNING requires approval, INFO is advisory.
- All 15 anomaly types are explicitly handled.
"""

import hashlib
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from statistics import mean, stdev
from typing import List, Dict, Any, Optional
from django.utils import timezone

from apps.groups.models import Group, GroupMembership
from .models import ImportAnomaly


MANDATORY_FIELDS = ["title", "amount", "paid_by", "expense_date"]

SETTLEMENT_KEYWORDS = [
    "settlement", "settle", "paid back", "repaid", "reimbursement",
    "reimburse", "transfer", "money back",
]


class AnomalyDetectionEngine:
    """
    Runs all 15 anomaly checks against parsed CSV rows.

    Usage:
        engine = AnomalyDetectionEngine(group=group, rows=parsed_rows)
        anomalies = engine.detect_all()
    """

    def __init__(self, group: Group, rows: List[Dict[str, Any]], import_job=None):
        self.group = group
        self.rows = rows
        self.import_job = import_job
        self._existing_expenses_hashes = self._build_existing_hashes()
        self._member_emails = self._build_member_emails()
        self._member_timelines = self._build_member_timelines()
        self._amounts = [
            self._parse_amount(r.get("amount", ""))
            for r in rows
            if self._parse_amount(r.get("amount", "")) is not None
        ]

    def _build_existing_hashes(self) -> set:
        """Pre-compute hashes of all existing expenses for duplicate detection."""
        from apps.expenses.models import Expense
        hashes = set()
        for exp in Expense.objects.filter(group=self.group, is_deleted=False):
            key = f"{exp.title.lower().strip()}|{exp.amount}|{exp.expense_date}|{exp.paid_by.email.lower()}"
            hashes.add(hashlib.md5(key.encode()).hexdigest())
        return hashes

    def _build_member_emails(self) -> Dict[str, object]:
        """Build email/username/first_name → user mapping for all ever-members."""
        email_map = {}
        for mem in GroupMembership.objects.filter(group=self.group).select_related("user"):
            user = mem.user
            email_map[user.email.lower()] = user
            email_map[user.username.lower()] = user
            email_map[user.first_name.lower()] = user
        return email_map

    def _build_member_timelines(self) -> Dict[str, List[Dict]]:
        """Build identifier → [{joined_at, left_at}] for membership windows."""
        timelines = {}
        for mem in GroupMembership.objects.filter(group=self.group).select_related("user"):
            user = mem.user
            for identifier in [user.email.lower(), user.username.lower(), user.first_name.lower()]:
                if identifier not in timelines:
                    timelines[identifier] = []
                timelines[identifier].append({"joined_at": mem.joined_at, "left_at": mem.left_at})
        return timelines

    def _parse_amount(self, value: str) -> Optional[Decimal]:
        try:
            return Decimal(str(value).replace(",", "").strip())
        except (InvalidOperation, TypeError):
            return None

    def _parse_date(self, value: str) -> Optional[date]:
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(str(value).strip(), fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    def _is_member_active_on(self, email: str, expense_date: date) -> bool:
        """Check if user was an active member on expense_date."""
        timelines = self._member_timelines.get(email.lower(), [])
        for window in timelines:
            if window["joined_at"] <= expense_date:
                if window["left_at"] is None or window["left_at"] >= expense_date:
                    return True
        return False

    def _row_hash(self, row: Dict) -> str:
        payer_ref = str(row.get('paid_by', '')).strip().lower()
        resolved_user = self._member_emails.get(payer_ref)
        payer_email = resolved_user.email.lower() if resolved_user else payer_ref
        
        key = f"{str(row.get('title','')).lower().strip()}|{row.get('amount','')}|{row.get('expense_date','')}|{payer_email}"
        return hashlib.md5(key.encode()).hexdigest()

    def detect_all(self) -> List[ImportAnomaly]:
        """Run all 15 anomaly checks and return flat list of anomalies."""
        all_anomalies = []

        # Track row hashes for inter-row duplicate detection
        seen_hashes: Dict[str, int] = {}

        for i, row in enumerate(self.rows):
            row_num = i + 1
            anomalies_for_row = []

            # Check 13: Blank mandatory fields
            anomalies_for_row += self._check_blank_mandatory_fields(row, row_num)

            # Check 3: Negative values
            anomalies_for_row += self._check_negative_value(row, row_num)

            # Check 6: Invalid date
            anomalies_for_row += self._check_invalid_date(row, row_num)

            # Check 7: Future date
            anomalies_for_row += self._check_future_date(row, row_num)

            # Check 5: Missing payer
            anomalies_for_row += self._check_missing_payer(row, row_num)

            # Check 9: Unknown member
            anomalies_for_row += self._check_unknown_member(row, row_num)

            # Check 10: Member not active
            anomalies_for_row += self._check_member_not_active(row, row_num)

            # Check 4: Settlement as expense
            anomalies_for_row += self._check_settlement_as_expense(row, row_num)

            # Check 8: Currency mismatch
            anomalies_for_row += self._check_currency_mismatch(row, row_num)

            # Check 12: Malformed row
            anomalies_for_row += self._check_malformed_row(row, row_num)

            # Check 1: Exact duplicate (against DB)
            anomalies_for_row += self._check_exact_duplicate_db(row, row_num)

            # Check 11: Inconsistent split totals
            anomalies_for_row += self._check_inconsistent_split(row, row_num)

            # Check 15: Amount outlier
            anomalies_for_row += self._check_amount_outlier(row, row_num)

            # Check 1b: Intra-file duplicates
            row_hash = self._row_hash(row)
            if row_hash in seen_hashes:
                anomalies_for_row.append(
                    ImportAnomaly(
                        import_job=self.import_job,
                        row_number=row_num,
                        raw_data=row,
                        anomaly_type=ImportAnomaly.AnomalyType.DUPLICATE_EXACT,
                        severity=ImportAnomaly.Severity.ERROR,
                        description=f"Row {row_num} is an exact duplicate of row {seen_hashes[row_hash]} within this file.",
                        recommendation="Skip this row. If intentional, split into separate expenses.",
                    )
                )
            else:
                seen_hashes[row_hash] = row_num

            all_anomalies.extend(anomalies_for_row)

        # Check 2: Possible duplicates (near-matches)
        all_anomalies += self._check_possible_duplicates()

        # Check 14: Conflicting duplicates (same title/date, different amounts)
        all_anomalies += self._check_conflicting_duplicates()

        return all_anomalies

    def _check_blank_mandatory_fields(self, row: Dict, row_num: int) -> List:
        anomalies = []
        for field in MANDATORY_FIELDS:
            if not row.get(field) or str(row[field]).strip() == "":
                anomalies.append(
                    ImportAnomaly(
                        import_job=self.import_job,
                        row_number=row_num,
                        raw_data=row,
                        anomaly_type=ImportAnomaly.AnomalyType.BLANK_MANDATORY_FIELD,
                        severity=ImportAnomaly.Severity.ERROR,
                        description=f"Required field '{field}' is blank in row {row_num}.",
                        recommendation=f"Provide a value for '{field}' before importing this row.",
                    )
                )
        return anomalies

    def _check_negative_value(self, row: Dict, row_num: int) -> List:
        amount = self._parse_amount(row.get("amount", ""))
        if amount is not None and amount < 0:
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.NEGATIVE_VALUE,
                    severity=ImportAnomaly.Severity.ERROR,
                    description=f"Amount is negative ({amount}) in row {row_num}. Expenses must be positive.",
                    recommendation="Use the absolute value, or record this as a settlement if it's a refund.",
                )
            ]
        return []

    def _check_invalid_date(self, row: Dict, row_num: int) -> List:
        raw_date = row.get("expense_date", "")
        if raw_date and self._parse_date(str(raw_date)) is None:
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.INVALID_DATE,
                    severity=ImportAnomaly.Severity.ERROR,
                    description=f"Cannot parse date '{raw_date}' in row {row_num}. Supported formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY.",
                    recommendation="Correct the date format before importing.",
                )
            ]
        return []

    def _check_future_date(self, row: Dict, row_num: int) -> List:
        parsed = self._parse_date(str(row.get("expense_date", "")))
        if parsed and parsed > timezone.now().date():
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.FUTURE_DATE,
                    severity=ImportAnomaly.Severity.WARNING,
                    description=f"Expense date {parsed} is in the future (row {row_num}).",
                    recommendation="Verify this is intentional. Future-dated expenses can cause membership validation issues.",
                )
            ]
        return []

    def _check_missing_payer(self, row: Dict, row_num: int) -> List:
        if not row.get("paid_by") or str(row.get("paid_by", "")).strip() == "":
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.MISSING_PAYER,
                    severity=ImportAnomaly.Severity.ERROR,
                    description=f"No payer specified in row {row_num}.",
                    recommendation="Add the email or name of who paid for this expense.",
                )
            ]
        return []

    def _check_unknown_member(self, row: Dict, row_num: int) -> List:
        payer_email = str(row.get("paid_by", "")).strip().lower()
        if payer_email and payer_email not in self._member_emails:
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.UNKNOWN_MEMBER,
                    severity=ImportAnomaly.Severity.ERROR,
                    description=f"Payer '{payer_email}' in row {row_num} is not a member of this group.",
                    recommendation="Add this person to the group before importing, or correct the email.",
                )
            ]
        return []

    def _check_member_not_active(self, row: Dict, row_num: int) -> List:
        payer_email = str(row.get("paid_by", "")).strip().lower()
        expense_date = self._parse_date(str(row.get("expense_date", "")))

        if payer_email in self._member_emails and expense_date:
            if not self._is_member_active_on(payer_email, expense_date):
                return [
                    ImportAnomaly(
                        import_job=self.import_job,
                        row_number=row_num,
                        raw_data=row,
                        anomaly_type=ImportAnomaly.AnomalyType.MEMBER_NOT_ACTIVE,
                        severity=ImportAnomaly.Severity.ERROR,
                        description=(
                            f"'{payer_email}' was not an active member of this group on "
                            f"{expense_date} (row {row_num})."
                        ),
                        recommendation=(
                            "Check the membership timeline. This expense cannot be assigned to "
                            "a member outside their active period."
                        ),
                    )
                ]
        return []

    def _check_settlement_as_expense(self, row: Dict, row_num: int) -> List:
        title = str(row.get("title", "")).lower()
        description = str(row.get("description", "")).lower()
        text = f"{title} {description}"
        for keyword in SETTLEMENT_KEYWORDS:
            if keyword in text:
                return [
                    ImportAnomaly(
                        import_job=self.import_job,
                        row_number=row_num,
                        raw_data=row,
                        anomaly_type=ImportAnomaly.AnomalyType.SETTLEMENT_AS_EXPENSE,
                        severity=ImportAnomaly.Severity.WARNING,
                        description=f"Row {row_num} title/description suggests this may be a settlement, not an expense: '{row.get('title', '')}'.",
                        recommendation="If this is a settlement, record it in the Settlements section instead.",
                    )
                ]
        return []

    def _check_currency_mismatch(self, row: Dict, row_num: int) -> List:
        currency = str(row.get("currency", "")).strip().upper()
        group_currency = self.group.default_currency
        if currency and group_currency and currency != group_currency.code:
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.CURRENCY_MISMATCH,
                    severity=ImportAnomaly.Severity.WARNING,
                    description=(
                        f"Row {row_num} uses currency '{currency}' but group default is "
                        f"'{group_currency.code}'."
                    ),
                    recommendation="Provide an exchange rate or convert to the group's default currency.",
                )
            ]
        return []

    def _check_malformed_row(self, row: Dict, row_num: int) -> List:
        """Check for structural issues: too few columns, garbled data."""
        anomalies = []
        # Check for garbled amount
        amount_raw = str(row.get("amount", ""))
        if amount_raw and not any(c.isdigit() for c in amount_raw):
            anomalies.append(
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.MALFORMED_ROW,
                    severity=ImportAnomaly.Severity.ERROR,
                    description=f"Amount field '{amount_raw}' in row {row_num} contains no numeric characters.",
                    recommendation="Correct the amount field.",
                )
            )
        # Check for suspiciously short title
        title = str(row.get("title", ""))
        if title and len(title.strip()) < 2:
            anomalies.append(
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.MALFORMED_ROW,
                    severity=ImportAnomaly.Severity.WARNING,
                    description=f"Title '{title}' in row {row_num} is suspiciously short.",
                    recommendation="Provide a descriptive title for the expense.",
                )
            )
        return anomalies

    def _check_exact_duplicate_db(self, row: Dict, row_num: int) -> List:
        """Check if this row already exists in the database."""
        row_hash = self._row_hash(row)
        if row_hash in self._existing_expenses_hashes:
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.DUPLICATE_EXACT,
                    severity=ImportAnomaly.Severity.ERROR,
                    description=f"Row {row_num} matches an existing expense in the database (title, amount, date, payer all match).",
                    recommendation="Skip this row to avoid duplicate expense.",
                )
            ]
        return []

    def _check_inconsistent_split(self, row: Dict, row_num: int) -> List:
        """Check if provided splits sum to the expense total."""
        splits_raw = row.get("splits", "")
        amount = self._parse_amount(row.get("amount", ""))

        if not splits_raw or not amount:
            return []

        # Try to parse splits like "user1:50,user2:50" or JSON
        try:
            total_split = Decimal("0")
            parts = str(splits_raw).split(",")
            for part in parts:
                if ":" in part:
                    _, val = part.split(":", 1)
                    total_split += Decimal(val.strip())

            if total_split > 0 and abs(total_split - amount) > Decimal("0.05"):
                return [
                    ImportAnomaly(
                        import_job=self.import_job,
                        row_number=row_num,
                        raw_data=row,
                        anomaly_type=ImportAnomaly.AnomalyType.INCONSISTENT_SPLIT,
                        severity=ImportAnomaly.Severity.ERROR,
                        description=(
                            f"Split total ({total_split}) does not match expense amount ({amount}) in row {row_num}."
                        ),
                        recommendation="Ensure split amounts sum to the expense total.",
                    )
                ]
        except (InvalidOperation, ValueError):
            pass
        return []

    def _check_amount_outlier(self, row: Dict, row_num: int) -> List:
        """Flag amounts that are statistical outliers (>3 std devs from mean)."""
        amount = self._parse_amount(row.get("amount", ""))
        if amount is None or len(self._amounts) < 5:
            return []

        avg = mean(float(a) for a in self._amounts)
        std = stdev(float(a) for a in self._amounts)

        if std > 0 and abs(float(amount) - avg) > 3 * std:
            return [
                ImportAnomaly(
                    import_job=self.import_job,
                    row_number=row_num,
                    raw_data=row,
                    anomaly_type=ImportAnomaly.AnomalyType.AMOUNT_OUTLIER,
                    severity=ImportAnomaly.Severity.INFO,
                    description=(
                        f"Amount {amount} in row {row_num} is a statistical outlier "
                        f"(mean: {avg:.2f}, std: {std:.2f})."
                    ),
                    recommendation="Verify this amount is correct before importing.",
                )
            ]
        return []

    def _check_possible_duplicates(self) -> List:
        """Find rows that are similar but not identical (same title+date, different amount)."""
        anomalies = []
        seen: Dict[str, int] = {}

        for i, row in enumerate(self.rows):
            row_num = i + 1
            # Fuzzy key: title (normalized) + date
            title = str(row.get("title", "")).lower().strip()
            date_str = str(row.get("expense_date", "")).strip()
            key = f"{title}|{date_str}"

            if key in seen:
                # Check if amounts differ (truly possible dup vs exact dup)
                prev_row = self.rows[seen[key] - 1]
                prev_amt = self._parse_amount(prev_row.get("amount", ""))
                curr_amt = self._parse_amount(row.get("amount", ""))

                if prev_amt != curr_amt and prev_amt is not None:
                    anomalies.append(
                        ImportAnomaly(
                            import_job=self.import_job,
                            row_number=row_num,
                            raw_data=row,
                            anomaly_type=ImportAnomaly.AnomalyType.DUPLICATE_POSSIBLE,
                            severity=ImportAnomaly.Severity.WARNING,
                            description=(
                                f"Row {row_num} has the same title and date as row {seen[key]} "
                                f"but different amount ({curr_amt} vs {prev_amt})."
                            ),
                            recommendation=(
                                "Review both rows. If these are different expenses, "
                                "add more descriptive titles to distinguish them."
                            ),
                        )
                    )
            else:
                seen[key] = row_num

        return anomalies

    def _check_conflicting_duplicates(self) -> List:
        """Find rows with same title+payer but different dates, suggesting data entry errors."""
        anomalies = []
        seen: Dict[str, int] = {}

        for i, row in enumerate(self.rows):
            row_num = i + 1
            title = str(row.get("title", "")).lower().strip()
            payer = str(row.get("paid_by", "")).lower().strip()
            amount = str(row.get("amount", "")).strip()
            key = f"{title}|{payer}|{amount}"

            if key in seen:
                prev_row = self.rows[seen[key] - 1]
                prev_date = str(prev_row.get("expense_date", ""))
                curr_date = str(row.get("expense_date", ""))

                if prev_date != curr_date:
                    anomalies.append(
                        ImportAnomaly(
                            import_job=self.import_job,
                            row_number=row_num,
                            raw_data=row,
                            anomaly_type=ImportAnomaly.AnomalyType.CONFLICTING_DUPLICATE,
                            severity=ImportAnomaly.Severity.WARNING,
                            description=(
                                f"Row {row_num} has same title, payer, and amount as row {seen[key]} "
                                f"but different dates ({curr_date} vs {prev_date})."
                            ),
                            recommendation=(
                                "Confirm whether these are two separate expenses or one expense "
                                "entered with different dates."
                            ),
                        )
                    )
            else:
                seen[key] = row_num

        return anomalies
