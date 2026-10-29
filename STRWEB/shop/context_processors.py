"""Template context: timezone, dates, calendar."""

import zoneinfo
from datetime import datetime
from datetime import timezone as dt_timezone

from django.utils import timezone

from shop.services import fetch_exchange_rate
from shop.utils import format_datetime_dd_mm_yyyy, text_calendar


def site_context(request):
    """Inject timezone, current dates, and FX rate."""

    server_now = datetime.now().astimezone()
    server_tz = server_now.tzinfo
    fx = fetch_exchange_rate('BYN', 'USD')

    return {
        'server_tz': server_tz,
        'server_datetime': format_datetime_dd_mm_yyyy(server_now, server_tz),
        'text_calendar': text_calendar(server_now.year, server_now.month),
        'fx_rate': fx.get('rate'),
    }
