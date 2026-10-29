"""REST API views — authenticated access only."""

import logging

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from shop.api.serializers import (
    ClientProfileSerializer,
    OrderSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    PromoCodeSerializer,
)
from shop.models import ClientProfile, Order, Product, ProductCategory, PromoCode

logger = logging.getLogger('shop.api')


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'manufacturer')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        logger.info('API create product by %s', self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        logger.info('API update product %s by %s', serializer.instance.pk, self.request.user)
        serializer.save()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('client').prefetch_related('items')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


class ClientProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClientProfile.objects.select_related('user')
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]


class PromoCodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAuthenticated]
