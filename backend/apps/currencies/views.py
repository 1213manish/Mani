from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Currency
from .serializers import CurrencySerializer


class CurrencyListView(generics.ListAPIView):
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    queryset = Currency.objects.filter(is_active=True)
