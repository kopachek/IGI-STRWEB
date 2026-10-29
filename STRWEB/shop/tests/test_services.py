from unittest.mock import MagicMock, patch

from shop.services import fetch_exchange_rate, fetch_public_holiday


@patch('shop.services.requests.get')
def test_fetch_exchange_rate_ok(mock_get):
    mock_get.return_value = MagicMock(
        ok=True,
        raise_for_status=lambda: None,
        json=lambda: {'rates': {'USD': 0.31}},
    )
    result = fetch_exchange_rate()
    assert result['ok'] is True
    assert result['rate'] == 0.31


@patch('shop.services.requests.get')
def test_fetch_holiday_api(mock_get):
    mock_get.return_value = MagicMock(
        ok=True,
        raise_for_status=lambda: None,
        json=lambda: [],
    )
    result = fetch_public_holiday(2024, 1, 1)
    assert result['ok'] is True
    assert result['is_holiday'] is False
