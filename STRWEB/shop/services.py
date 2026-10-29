"""External HTTP API integrations."""

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger('shop.external')


def fetch_exchange_rate(base: str = 'BYN', target: str = 'USD') -> dict[str, Any]:
    """
    Fetch exchange rate from open.er-api.com (free, no key required).
    Used to show approximate USD prices for products.
    """
    url = f'https://open.er-api.com/v6/latest/{base}'
    try:
        response = requests.get(url, timeout=settings.EXTERNAL_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        rate = data.get('rates', {}).get(target)
        logger.info('Exchange rate %s->%s: %s', base, target, rate)
        return {'base': base, 'target': target, 'rate': rate, 'ok': rate is not None}
    except requests.RequestException as exc:
        logger.warning('Exchange API failed: %s', exc)
        return {'base': base, 'target': target, 'rate': None, 'ok': False, 'error': str(exc)}


def fetch_public_holiday(year: int, month: int, day: int) -> dict[str, Any]:
    """
    Check if date is a public holiday via Nager.Date API.
    Useful for delivery date planning hints.
    """
    url = f'https://date.nager.at/api/v3/PublicHolidays/{year}/BY'
    try:
        response = requests.get(url, timeout=settings.EXTERNAL_API_TIMEOUT)
        response.raise_for_status()
        holidays = response.json()
        iso = f'{year:04d}-{month:02d}-{day:02d}'
        match = [h for h in holidays if h.get('date') == iso]
        logger.info('Holiday check for %s: %s', iso, bool(match))
        return {'date': iso, 'is_holiday': bool(match), 'name': match[0]['localName'] if match else None, 'ok': True}
    except requests.RequestException as exc:
        logger.warning('Holiday API failed: %s', exc)
        return {'date': f'{year:04d}-{month:02d}-{day:02d}', 'is_holiday': False, 'ok': False, 'error': str(exc)}
