from datetime import date

import pytest
from django.contrib.auth.models import User

from shop.models import ClientProfile, EmployeeProfile, Product, ProductCategory


@pytest.fixture
def category(db):
    return ProductCategory.objects.create(name='Cakes', description='Test')


@pytest.fixture
def product(db, category):
    return Product.objects.create(name='Test Cake', price='10.00', unit='pcs', category=category)


@pytest.fixture
def user(db):
    u = User.objects.create_user(username='testuser', password='pass12345')
    ClientProfile.objects.create(
        user=u,
        phone='+375 (29) 100-00-01',
        email='test@mail.by',
        birth_date=date(1995, 6, 1),
    )
    return u


@pytest.fixture
def employee_user(db):
    u = User.objects.create_user(username='emp', password='pass12345', is_staff=True)
    EmployeeProfile.objects.create(
        user=u,
        phone='+375 (33) 200-00-02',
        birth_date=date(1990, 1, 1),
        position='Manager',
    )
    return u


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser('admin', 'a@a.by', 'adminpass')
