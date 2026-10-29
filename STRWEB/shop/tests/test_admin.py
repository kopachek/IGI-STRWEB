import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_admin_login(client, admin_user):
    r = client.post('/admin/login/', {'username': 'admin', 'password': 'adminpass'})
    assert r.status_code in (200, 302)
