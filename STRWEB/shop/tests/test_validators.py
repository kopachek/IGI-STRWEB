from datetime import date

import pytest
from django.core.exceptions import ValidationError

from shop.validators import validate_adult_age, validate_belarus_phone


@pytest.mark.parametrize(
    'phone',
    ['+375 29 123-45-67', '+375339998877', '+375 (44) 100-20-30'],
)
def test_valid_phone(phone):
    validate_belarus_phone(phone)


@pytest.mark.parametrize('phone', ['80291234567', '375291234567', 'invalid'])
def test_invalid_phone(phone):
    with pytest.raises(ValidationError):
        validate_belarus_phone(phone)


def test_adult_ok():
    validate_adult_age(date(1990, 1, 1))


def test_underage():
    with pytest.raises(ValidationError):
        validate_adult_age(date.today().replace(year=date.today().year - 10))
