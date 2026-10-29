from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from shop.models import ClientProfile, Order, OrderItem, Product, ProductCategory
from shop.utils import build_category_chart_base64


@pytest.mark.django_db
def test_category_chart_with_data(product):
    user = User.objects.create_user('c2', password='x')
    client = ClientProfile.objects.create(
        user=user, phone='+375 (29) 101-01-01', email='c2@by', birth_date=date(1992, 1, 1)
    )
    order = Order.objects.create(client=client, delivery_date=date.today())
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price=product.price)
    chart = build_category_chart_base64()
    assert len(chart) > 100

