"""
Expenses views.
"""

from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from apps.groups.models import Group, GroupMembership
from .models import Expense
from .serializers import ExpenseSerializer, ExpenseCreateSerializer


def get_member_group_or_404(user, group_id):
    """Return group only if user is an active member."""
    return get_object_or_404(
        Group,
        id=group_id,
        memberships__user=user,
        memberships__left_at__isnull=True,
        is_active=True,
    )


@extend_schema(tags=["Expenses"])
class GroupExpenseListCreateView(generics.ListCreateAPIView):
    """List or create expenses for a group."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ExpenseCreateSerializer
        return ExpenseSerializer

    def get_queryset(self):
        group = get_member_group_or_404(self.request.user, self.kwargs["group_id"])
        return Expense.objects.filter(
            group=group, is_deleted=False
        ).select_related(
            "paid_by", "currency", "original_currency", "created_by"
        ).prefetch_related("splits__user")

    def create(self, request, *args, **kwargs):
        # Inject group into request data
        group = get_member_group_or_404(request.user, self.kwargs["group_id"])
        data = request.data.copy()
        data["group"] = str(group.id)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()
        return Response(
            ExpenseSerializer(expense).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Expenses"])
class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or soft-delete an expense."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # User must be a member of the expense's group
        return Expense.objects.filter(
            group__memberships__user=self.request.user,
            group__memberships__left_at__isnull=True,
            is_deleted=False,
        ).select_related(
            "paid_by", "currency", "original_currency", "created_by"
        ).prefetch_related("splits__user").distinct()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ExpenseCreateSerializer
        return ExpenseSerializer

    def destroy(self, request, *args, **kwargs):
        expense = self.get_object()
        expense.is_deleted = True
        expense.deleted_at = timezone.now()
        expense.deleted_by = request.user
        expense.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
        return Response(status=status.HTTP_204_NO_CONTENT)
