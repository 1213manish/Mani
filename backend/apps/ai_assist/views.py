"""
AI Assist views: OpenAI-powered explanations and suggestions.

DESIGN PRINCIPLES:
1. AI suggestions are READ-ONLY — they never modify data.
2. Every suggestion requires explicit user approval.
3. API key comes from settings (never hardcoded).
4. If OpenAI is unavailable, graceful degradation — return None/error.
5. All prompts are carefully engineered to return structured, safe responses.
"""

from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from apps.groups.models import Group
from apps.balances.engine import BalanceEngine
from apps.imports.models import ImportAnomaly


def get_openai_client():
    """Return an OpenAI client if API key is configured."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-key-here":
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception:
        return None


def call_openai(client, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
    """Call OpenAI and return response text. Returns None on failure."""
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return None


@extend_schema(tags=["AI Assist"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def explain_balance_ai_view(request):
    """
    AI-powered natural language explanation of a user's balance.

    Request: { "group_id": "uuid", "user_id": "uuid" (optional) }
    Response: { "explanation": "...", "source": "ai" | "fallback" }

    AI suggestions never modify data. Read-only.
    """
    group_id = request.data.get("group_id")
    user_id = request.data.get("user_id", str(request.user.id))

    if not group_id:
        return Response({"error": "group_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    group = get_object_or_404(
        Group, id=group_id,
        memberships__user=request.user, memberships__left_at__isnull=True,
    )

    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    engine = BalanceEngine(group)
    explanation_data = engine.explain_balance(target_user)

    # Build context for AI
    net = explanation_data["net_balance"]
    expense_count = len(explanation_data["expense_breakdown"])
    expense_details = "\n".join(
        [
            f"- {e['title']} ({e['expense_date']}): your share {e['your_share']}"
            for e in explanation_data["expense_breakdown"][:10]
        ]
    )

    client = get_openai_client()

    if client:
        system_prompt = (
            "You are a helpful financial assistant for a shared expense app. "
            "Explain the user's balance in simple, friendly language. "
            "Be specific about the expenses. Never suggest modifying data. "
            "Keep the explanation under 150 words."
        )
        user_prompt = (
            f"User: {target_user.full_name}\n"
            f"Group: {group.name}\n"
            f"Net Balance: {net} (positive = others owe them, negative = they owe others)\n"
            f"Number of contributing expenses: {expense_count}\n"
            f"Top expenses:\n{expense_details}\n\n"
            "Explain this balance in simple terms."
        )
        ai_text = call_openai(client, system_prompt, user_prompt)

        if ai_text:
            return Response(
                {
                    "explanation": ai_text,
                    "source": "ai",
                    "data": explanation_data,
                    "disclaimer": "This is an AI-generated explanation. No data was modified.",
                }
            )

    # Fallback: template-based explanation
    net_decimal = Decimal(str(net))
    if net_decimal > 0:
        fallback = (
            f"{target_user.full_name} is owed ₹{abs(net_decimal):.2f} across "
            f"{expense_count} expense(s) in '{group.name}'. "
            "Others owe them money."
        )
    elif net_decimal < 0:
        fallback = (
            f"{target_user.full_name} owes ₹{abs(net_decimal):.2f} across "
            f"{expense_count} expense(s) in '{group.name}'."
        )
    else:
        fallback = f"{target_user.full_name} is fully settled up in '{group.name}'."

    return Response(
        {
            "explanation": fallback,
            "source": "fallback",
            "data": explanation_data,
            "disclaimer": "AI is not configured. Showing template explanation.",
        }
    )


@extend_schema(tags=["AI Assist"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def explain_anomaly_ai_view(request):
    """
    AI-powered explanation of a detected import anomaly.

    Request: { "anomaly_id": "uuid" }
    Response: { "explanation": "...", "suggestion": "..." }

    Never modifies data. User approval required for any action.
    """
    anomaly_id = request.data.get("anomaly_id")
    if not anomaly_id:
        return Response({"error": "anomaly_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    anomaly = get_object_or_404(
        ImportAnomaly, id=anomaly_id,
        import_job__group__memberships__user=request.user,
        import_job__group__memberships__left_at__isnull=True,
    )

    client = get_openai_client()

    if client:
        system_prompt = (
            "You are a data quality expert for a shared expense management app. "
            "Explain the detected anomaly clearly and suggest how to resolve it. "
            "Do NOT suggest automatic data changes — user approval is always required. "
            "Be concise and practical. Under 100 words."
        )
        user_prompt = (
            f"Anomaly Type: {anomaly.anomaly_type}\n"
            f"Severity: {anomaly.severity}\n"
            f"Description: {anomaly.description}\n"
            f"Row Data: {anomaly.raw_data}\n\n"
            "Explain this anomaly and how the user should resolve it."
        )
        ai_text = call_openai(client, system_prompt, user_prompt, max_tokens=200)

        if ai_text:
            return Response(
                {
                    "explanation": ai_text,
                    "source": "ai",
                    "recommendation": anomaly.recommendation,
                    "disclaimer": "AI suggestion only. No changes have been made.",
                }
            )

    return Response(
        {
            "explanation": anomaly.description,
            "source": "fallback",
            "recommendation": anomaly.recommendation,
            "disclaimer": "AI is not configured.",
        }
    )


@extend_schema(tags=["AI Assist"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def suggest_resolution_ai_view(request):
    """
    AI-powered suggestion for resolving a specific anomaly.

    Returns suggested action — never auto-applies it.
    User must explicitly approve via the anomaly resolve endpoint.
    """
    anomaly_id = request.data.get("anomaly_id")
    if not anomaly_id:
        return Response({"error": "anomaly_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    anomaly = get_object_or_404(
        ImportAnomaly, id=anomaly_id,
        import_job__group__memberships__user=request.user,
        import_job__group__memberships__left_at__isnull=True,
    )

    client = get_openai_client()

    suggested_action = None
    if client:
        system_prompt = (
            "You are a data quality expert. Given the anomaly details, "
            "suggest ONE specific action: either 'APPROVE' (import this row) or "
            "'REJECT' (skip this row). Explain your reasoning briefly. "
            "Format: ACTION: [APPROVE/REJECT]\nREASON: [brief reason]"
        )
        user_prompt = (
            f"Anomaly: {anomaly.anomaly_type} ({anomaly.severity})\n"
            f"Description: {anomaly.description}\n"
            f"Row: {anomaly.raw_data}"
        )
        ai_text = call_openai(client, system_prompt, user_prompt, max_tokens=150)
        if ai_text:
            suggested_action = ai_text

    return Response(
        {
            "suggested_action": suggested_action or anomaly.recommendation,
            "source": "ai" if suggested_action else "fallback",
            "anomaly_id": str(anomaly.id),
            "disclaimer": (
                "This is an AI SUGGESTION only. No data has been changed. "
                "You must explicitly approve or reject via the resolve endpoint."
            ),
        }
    )
