from datetime import datetime, timezone as dt_timezone

import pytest
from django.utils import timezone

from shop.utils import format_date_dd_mm_yyyy, sales_statistics, text_calendar


def test_format_date():
    dt = datetime(2024, 3, 5, 12, 0, tzinfo=dt_timezone.utc)
    assert format_date_dd_mm_yyyy(dt) == '05/03/2024'


def test_text_calendar():
    cal = text_calendar(2024, 3)
    assert 'March' in cal
    assert '2024' in cal


@pytest.mark.django_db
def test_sales_statistics_empty():
    stats = sales_statistics()
    assert stats['total_sales'] == 0
    assert stats['sales_mean'] == 0
