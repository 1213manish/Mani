# Technical Design Decisions

This document records every significant design decision made in ExpenseFlow, including rationale and trade-offs considered.

---

## D-001: Email as Primary Identifier, Not Username

**Decision**: Use email as the `USERNAME_FIELD`. Username exists but is not used for authentication.

**Rationale**: Users forget usernames. Email is universally unique and is the natural login identifier in modern apps. Reduces "I forgot my username" support burden.

**Trade-off**: Usernames still exist for display purposes (legacy data migration ease).

---

## D-002: UUID Primary Keys on All Models

**Decision**: All models use `UUID` primary keys (via `BaseModel`).

**Rationale**:
- No information leakage (sequential IDs expose row counts, business metrics)
- No merge conflicts in distributed systems
- Safe to expose in URLs

**Trade-off**: Slightly larger index size. Negligible at expected scale.

---

## D-003: Membership Timeline as Source of Truth

**Decision**: `GroupMembership` stores `joined_at` and `left_at` (nullable). Every expense validation checks these dates.

**Rationale**: Real groups have changing membership. An expense paid on March 15 should not count against someone who joined April 1, or someone who left January 31. This prevents silent data integrity violations.

**Implementation**: `Group.get_active_members(date)` and `Group.is_member(user, date)` are the canonical query methods. The balance engine and expense serializer both use these.

---

## D-004: Balances Are Computed, Never Stored

**Decision**: No `Balance` model. All balances are computed on-demand from expenses and settlements.

**Rationale**:
- No cache invalidation bugs
- No stale balance states
- Balances are always perfectly consistent with the underlying data
- Explainability is structural, not audited separately

**Trade-off**: Slightly higher DB load per balance query. Acceptable at current scale. Can add materialized views or Redis caching later.

---

## D-005: O(n log n) Debt Minimization

**Decision**: Use a greedy two-heap algorithm to minimize settlement transactions.

**Rationale**: The naive approach produces n-1 transactions. The greedy algorithm (maintain max-heap of creditors, max-heap of debtors, match greedily) reduces to the minimum provably optimal solution for most real-world cases.

**Implementation**: `apps/balances/engine.py:simplify_debts()`

---

## D-006: Settlements Separate from Expenses

**Decision**: `Settlement` is its own model, separate from `Expense`.

**Rationale**: Settlements are not expenses. They don't have split types, categories, receipts, or payers/owed-to relationships. Mixing them would complicate queries, reporting, and anomaly detection.

**Implementation**: Balance engine applies settlements after expenses: `net[payer] += amount; net[receiver] -= amount`.

---

## D-007: Import Files Are Never Modified

**Decision**: Uploaded CSV files are stored as-is with a SHA-256 hash. The import pipeline reads them for analysis but never writes to them.

**Rationale**: Auditability. Users must be able to verify their original data was not tampered with.

**Implementation**: Files stored in `MEDIA_ROOT/imports/{group_id}/{hash}_{filename}`. Hash is also used to prevent duplicate imports.

---

## D-008: 15 Anomaly Types with Severity Tiers

**Decision**: Anomalies have three severity levels:
- `ERROR`: Blocks import — must resolve before executing
- `WARNING`: Requires acknowledgment but can be approved
- `INFO`: Advisory only, does not block

**Rationale**: Not all anomalies are equal. A negative amount is always wrong. A future-dated expense might be intentional. A statistical outlier should be flagged but not blocked.

---

## D-009: AI Is Read-Only

**Decision**: AI endpoints return suggestions only. No AI endpoint ever creates, updates, or deletes data.

**Rationale**: Explainability and user trust. Every financial action must be explicitly user-initiated. AI suggestions can be wrong; making them automatic would be dangerous.

**Implementation**: All AI responses include a `disclaimer` field. Users must explicitly call the approve/reject endpoint to act on suggestions.

---

## D-010: Audit Log Is Append-Only

**Decision**: `AuditLog` records are never deleted or updated in application code.

**Rationale**: An audit log that can be deleted is not an audit log. Every financial action must be permanently traceable.

**Implementation**: No `update_fields` or `delete()` calls on `AuditLog`. Django admin can be further locked if needed.

---

## D-011: INR-Only for This Deployment

**Decision**: Group default currency is INR. Multi-currency is architecturally supported (exchange rate stored per expense) but the UI is INR-first.

**Rationale**: User preference ("keep it INR only"). The backend fully supports multi-currency with `original_amount`, `original_currency`, `exchange_rate`, and `converted_amount` fields.

---

## D-012: Console Email Backend for Development

**Decision**: `EMAIL_BACKEND = django.core.mail.backends.console.EmailBackend` in dev settings.

**Rationale**: No email service setup required for development. Emails print to the terminal.

---

## D-013: Custom Exception Handler

**Decision**: Implemented a global `custom_exception_handler` in `apps/core/exceptions.py`.

**Rationale**: Consistent API error format. All errors return `{error, code, details}`. Makes frontend error handling deterministic.

---

## D-014: `SoftDeleteModel` for Data Integrity

**Decision**: Expenses use `is_deleted` flag instead of actual deletion.

**Rationale**: Deleted expenses affect historical balances. Soft-delete preserves audit trails and allows recovery. Hard deletes are irreversible.

---

## D-015: Zero-Sum Balance Invariant

**Decision**: The balance engine enforces that `sum(all_net_balances) == 0` at all times.

**Rationale**: Conservation of money. What one person is owed, others owe. If this invariant breaks, there's a data integrity bug. Tests verify this invariant explicitly.
