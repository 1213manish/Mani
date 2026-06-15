# Project Scope & Anomaly Log

This document detail the anomaly detection capabilities of the import pipeline and the underlying database schema.

---

## 1. Anomaly Log (CSV Data Issues)

Our import pipeline implements **15 distinct anomaly checks** categorized by severity. Every problem found in a CSV is logged as an `ImportAnomaly` record requiring specific user actions.

### Severity Tiers:
- 🔴 **ERROR**: Blocks import. Row cannot be ingested until the CSV is fixed or the system logic is updated.
- 🟡 **WARNING**: Potentially valid but suspicious. Requires explicit user approval/acknowledgment.
- 🔵 **INFO**: Purely advisory. Does not block ingestion.

### The 15 Checks:

| # | Anomaly Type | Severity | Logic & Handling |
|---|---|---|---|
| 1 | **Exact Duplicate (DB)** | 🔴 ERROR | Matches `title`, `amount`, `date`, and `payer` exactly against an existing record in the database. Prevents double-entry. |
| 2 | **Intra-file Duplicate** | 🔴 ERROR | Identifies identical rows within the same uploaded CSV file. |
| 3 | **Negative Value** | 🔴 ERROR | Amounts must be positive. Negative values usually indicate a miscategorized refund or data entry error. |
| 4 | **Settlement as Expense** | 🟡 WARNING | Scans title for keywords like "settlement", "paid back", or "repay". Suggests converting to a `Settlement` record instead of an `Expense`. |
| 5 | **Missing Payer** | 🔴 ERROR | Row contains amount/title but the `paid_by` field is empty. Blocking error. |
| 6 | **Invalid Date** | 🔴 ERROR | Date strings that cannot be parsed into a standard YYYY-MM-DD or DD/MM/YYYY format. |
| 7 | **Future Date** | 🟡 WARNING | Expense date is in the future. Allowed but flagged for user verification. |
| 8 | **Currency Mismatch** | 🟡 WARNING | Expense currency differs from the majority of the file or the group's default currency. |
| 9 | **Unknown Member** | 🔴 ERROR | Payer email or name does not match any current or former member of the group. |
| 10 | **Inactive Member** | 🔴 ERROR | Member exists, but the expense date is before they joined or after they left the group. |
| 11 | **Inconsistent Split** | 🔴 ERROR | For rows providing explicit split amounts, the sum of splits does not equal the total amount. |
| 12 | **Malformed Row** | 🔴 ERROR | Row has fewer columns or corrupted data structure compared to the header. |
| 13 | **Blank Mandatory Fields** | 🔴 ERROR | Title, Date, or Amount is explicitly empty. |
| 14 | **Conflicting Duplicate** | 🟡 WARNING | Same title and date, but different amount. Suggests a possible correction or related but distinct expense. |
| 15 | **Statistical Outlier** | 🔵 INFO | Amount is > 3 standard deviations from the group's mean spending. Flags high-value items for review. |

---

## 2. Database Schema

The system uses a relational PostgreSQL schema (implemented via Django ORM) with **UUIDs** as primary keys for security and distributed safety.

### Core Entities:

1. **Accounts (User)**
   - Custom user model using `email` as the unique identifier.
   - Profile metadata and status.

2. **Groups**
   - The primary organizational unit.
   - Tracks default currency and group metadata.

3. **GroupMembership**
   - Junction table between `User` and `Group`.
   - **Critical Fields**: `joined_at`, `left_at` (used for timeline-aware expense validation).
   - Role management (Admin/Member).

4. **Expenses**
   - Records the money spent.
   - Links to `Payer` (User) and `Group`.
   - Supports 4 split types: `EQUALLY`, `EXACT`, `PERCENTAGE`, `SHARES`.
   - Stores `original_amount` and `converted_amount` for multi-currency support.

5. **Settlements**
   - Represents money moving between users to "square up".
   - Distinct from expenses to maintain pure debt/credit logic.

6. **ImportJobs & ImportAnomalies**
   - Tracks CSV file metadata (SHA-256 hash to prevent re-uploads).
   - Persistent log of every anomaly found per file.

7. **AuditLog** (Append-only)
   - Immutable record of every mutation (Create/Update/Delete).
   - Captures actor, timestamp, IP address, and before/after state snapshots.
