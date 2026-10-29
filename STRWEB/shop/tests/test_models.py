from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from shop.models import ClientProfile, Order, OrderItem, Product, ProductCategory


@pytest.mark.django_db
def test_product_str(category):
    p = Product.objects.create(name='Eclair', price='3.00', unit='pcs', category=category)
    assert 'Eclair' in str(p)


@pytest.mark.django_db
def test_order_totals(user, product):
    client = user.client_profile
    order = Order.objects.create(client=client, delivery_date=date.today(), delivery_cost=Decimal('5'))
    OrderItem.objects.create(order=order, product=product, quantity=2, unit_price=product.price)
    assert order.items_total == Decimal('20.00')
    assert order.grand_total == Decimal('25.00')


@pytest.mark.django_db
def test_client_age(user):
    assert user.client_profile.age >= 18
