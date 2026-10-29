import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from shop.models import Product


@pytest.mark.django_db
def test_api_products_requires_auth(product):
    client = APIClient()
    url = reverse('product-list')
    r = client.get(url)
    assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_api_products_authenticated(user, product):
    client = APIClient()
    client.login(username='testuser', password='pass12345')
    url = '/api/products/'
    r = client.get(url)
    assert r.status_code == status.HTTP_200_OK
    assert len(r.json()) >= 1


@pytest.mark.django_db
def test_api_categories(user, category):
    client = APIClient()
    client.login(username='testuser', password='pass12345')
    r = client.get('/api/categories/')
    assert r.status_code == 200
