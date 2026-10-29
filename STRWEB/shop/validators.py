import re
from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


PHONE_PATTERN = re.compile(r'^\+375\s*\(?\s*(29|33|44|25)\s*\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}$')


def validate_belarus_phone(value: str) -> None:
    if not PHONE_PATTERN.match(value or ''):
        raise ValidationError(
            _('Phone must match format +375 (29) XXX-XX-XX.'),
            code='invalid_phone',
        )


def validate_adult_age(birth_date: date) -> None:
    if birth_date is None:
        raise ValidationError(_('Birth date is required.'), code='required')
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < 18:
        raise ValidationError(_('Must be at least 18 years old.'), code='underage')
