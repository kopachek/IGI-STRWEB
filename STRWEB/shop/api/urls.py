from django.urls import include, path
from rest_framework.routers import DefaultRouter

from shop.api.views import (
    ClientProfileViewSet,
    OrderViewSet,
    ProductCategoryViewSet,
    ProductViewSet,
    PromoCodeViewSet,
)

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'clients', ClientProfileViewSet)
router.register(r'promo-codes', PromoCodeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
