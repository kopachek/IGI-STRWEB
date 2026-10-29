import pytest

from shop.forms import CustomerRegistrationForm, ReviewForm


@pytest.mark.django_db
def test_review_form_valid():
    form = ReviewForm(data={'rating': 5, 'text': 'Great shop, loved it!'})
    assert form.is_valid()


@pytest.mark.django_db
def test_registration_invalid_phone():
    form = CustomerRegistrationForm(
        data={
            'username': 'new1',
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.by',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'phone': 'bad',
            'birth_date': '1995-01-01',
        }
    )
    assert not form.is_valid()
