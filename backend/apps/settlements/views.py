from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

from apps.groups.models import Group
from .models import Settlement
from .serializers import SettlementSerializer, SettlementCreateSerializer


def get_member_group_or_404(user, group_id):
    return get_object_or_404(
        Group, id=group_id,
        memberships__user=user, memberships__left_at__isnull=True, is_active=True,
    )


@extend_schema(tags=["Settlements"])
class GroupSettlementListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SettlementCreateSerializer
        return SettlementSerializer

    def get_queryset(self):
        group = get_member_group_or_404(self.request.user, self.kwargs["group_id"])
        return Settlement.objects.filter(
            group=group
        ).select_related("payer", "receiver", "currency", "created_by")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["group"] = get_member_group_or_404(self.request.user, self.kwargs["group_id"])
        return ctx

    def create(self, request, *args, **kwargs):
        group = get_member_group_or_404(request.user, self.kwargs["group_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settlement = serializer.save()
        return Response(
            SettlementSerializer(settlement).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Settlements"])
class SettlementDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SettlementSerializer

    def get_queryset(self):
        return Settlement.objects.filter(
            group__memberships__user=self.request.user,
            group__memberships__left_at__isnull=True,
        ).select_related("payer", "receiver", "currency", "created_by").distinct()
