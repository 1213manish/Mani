# AI Usage and Integration Documentation

The **ExpenseFlow** platform includes an intelligent AI Assist module powered by OpenAI (`gpt-4o-mini`). This module provides natural language explanations for balances and anomaly detections, as well as resolution suggestions during CSV imports.

---

## 1. Architectural Design Principles

To ensure complete data safety, auditability, and deterministic operations, the AI Assist module adheres to the following core engineering rules:

1. **Read-Only Operation**: The AI engine is strictly read-only. It has no capabilities, database permissions, or API routing to modify, delete, or create expenses, settlements, memberships, or groups.
2. **Explicit User Approval Required**: Any resolution or action suggested by the AI must be manually and explicitly approved by a group administrator or user. The app will never auto-apply or execute AI suggestions.
3. **Secure Secrets Management**: The API client loads the `OPENAI_API_KEY` from system environment variables via `python-decouple`. Secrets are never committed to version control.
4. **Graceful Fallback & Zero Dependency**: If no API key is provided, or the OpenAI service is down/rate-limited, the system gracefully falls back to deterministic, template-based logic without disrupting core application features.
5. **Deterministic Disclaimer Delivery**: Every endpoint returned from the AI module contains a mandatory `disclaimer` field explaining that the text is an AI-generated suggestion and that no changes were made.

---

## 2. AI endpoints

The AI Assist features are served through three dedicated API endpoints:

### A. Explain Balance
- **Endpoint**: `POST /api/ai/explain-balance/`
- **Permissions**: Is Group Member
- **Input**: `{ "group_id": "<uuid>", "user_id": "<uuid>" (optional) }`
- **Behavior**: Retrieves the full expense breakdown and transaction graph for the target user from the `BalanceEngine`, compiles the details, and prompts the AI to draft a human-friendly narrative of why they owe or are owed that specific amount.
- **Fallback**: Returns a structured string summarizing total amounts owed or owing, backed by a template.

### B. Explain Anomaly
- **Endpoint**: `POST /api/ai/explain-anomaly/`
- **Permissions**: Is Group Member
- **Input**: `{ "anomaly_id": "<uuid>" }`
- **Behavior**: Provides details on a detected import anomaly (e.g., negative value, settlement posted as expense, duplicate) and returns a human-friendly description of why the parser flagged it.
- **Fallback**: Returns the raw database description of the flagged anomaly.

### C. Suggest Resolution
- **Endpoint**: `POST /api/ai/suggest-resolution/`
- **Permissions**: Is Group Member
- **Input**: `{ "anomaly_id": "<uuid>" }`
- **Behavior**: Prompts the AI to recommend a specific triage choice—either `APPROVE` (import the CSV row despite warnings) or `REJECT` (exclude the row).
- **Fallback**: Displays the database-configured default recommendation (e.g., "Exclude row from import or fix date format").

---

## 3. Prompt Engineering Context

To achieve high-quality responses under low latency, we pass structured contextual variables to the LLM:

### Balance Explanation Prompt
* **System Prompt**:
  > You are a helpful financial assistant for a shared expense app. Explain the user's balance in simple, friendly language. Be specific about the expenses. Never suggest modifying data. Keep the explanation under 150 words.
* **User Prompt**:
  > User: Aisha Patel  
  > Group: Goa Trip 2024  
  > Net Balance: 2350.00 (positive = others owe them, negative = they owe others)  
  > Number of contributing expenses: 3  
  > Top expenses:  
  > - Villa Rent (2026-06-12): your share 1500.00  
  > - Dinner (2026-06-13): your share 450.00  
  >   
  > Explain this balance in simple terms.

### Import Anomaly Explanation Prompt
* **System Prompt**:
  > You are a data quality expert for a shared expense management app. Explain the detected anomaly clearly and suggest how to resolve it. Do NOT suggest automatic data changes — user approval is always required. Be concise and practical. Under 100 words.
* **User Prompt**:
  > Anomaly Type: NEGATIVE_VALUE  
  > Severity: ERROR  
  > Description: Amount cannot be negative (-500.00)  
  > Row Data: {"title": "Refund", "amount": "-500.00", "payer": "rohan@example.com"}  
  >   
  > Explain this anomaly and how the user should resolve it.

---

## 4. Fallback Execution Verification

When the `OPENAI_API_KEY` is not present, the `get_openai_client()` function returns `None` safely. The view routes instantly skip external network calls:

```python
client = get_openai_client()
if client:
    # Try calling OpenAI API
    ...
# Fallback logic handles standard execution paths with 100% availability
```
This guarantees local development, offline runs, and environments without an OpenAI subscription are fully functional.
