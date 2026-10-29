from datetime import date

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home(client):
    r = client.get(reverse('home'))
    assert r.status_code == 200


@pytest.mark.django_db
def test_product_list_guest(client, product):
    r = client.get(reverse('product_list'))
    assert r.status_code == 200
    assert product.name.encode() in r.content or product.name in r.content.decode()


@pytest.mark.django_db
def test_product_filter_by_price(client, product):
    r = client.get(reverse('product_list'), {'min_price': '5', 'max_price': '20'})
    assert r.status_code == 200


@pytest.mark.django_db
def test_privacy(client):
    assert client.get(reverse('privacy')).status_code == 200


@pytest.mark.django_db
def test_promos(client):
    assert client.get(reverse('promos')).status_code == 200


@pytest.mark.django_db
def test_statistics(client):
    assert client.get(reverse('statistics')).status_code == 200


@pytest.mark.django_db
def test_checkout_requires_login(client):
    r = client.get(reverse('checkout'))
    assert r.status_code == 302


@pytest.mark.django_db
def test_checkout_logged_in(client, user, product):
    client.login(username='testuser', password='pass12345')
    r = client.get(reverse('checkout'))
    assert r.status_code == 200


@pytest.mark.django_db
def test_employee_dashboard(client, employee_user):
    client.login(username='emp', password='pass12345')
    r = client.get(reverse('employee_dashboard'))
    assert r.status_code == 200


@pytest.mark.django_db
def test_review_add(client, user):
    client.login(username='testuser', password='pass12345')
    r = client.post(
        reverse('review_add'),
        {'rating': 4, 'text': 'Nice pastries and fast delivery.'},
    )
    assert r.status_code == 302


@pytest.mark.django_db
def test_register_page(client):
    assert client.get(reverse('register')).status_code == 200


@pytest.mark.django_db
def test_set_timezone(client):
    r = client.post(reverse('set_timezone'), {'timezone': 'Europe/Minsk'})
    assert r.status_code == 302
    assert client.session['django_timezone'] == 'Europe/Minsk'
