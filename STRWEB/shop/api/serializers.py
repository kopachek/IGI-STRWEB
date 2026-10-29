"""REST API serializers."""

from rest_framework import serializers

from shop.models import ClientProfile, Order, Product, ProductCategory, PromoCode


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'description')


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'price', 'unit', 'category', 'category_name',
            'description', 'is_available', 'created_at', 'updated_at',
        )


class ClientProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ClientProfile
        fields = ('id', 'username', 'phone', 'email', 'birth_date', 'address')


class OrderSerializer(serializers.ModelSerializer):
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'client', 'sale_date', 'delivery_date', 'delivery_cost',
            'grand_total', 'created_at', 'updated_at',
        )


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ('id', 'code', 'description', 'discount_percent', 'is_active', 'valid_from', 'valid_until')
