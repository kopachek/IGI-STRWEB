"""Utility helpers: dates, statistics, charts."""

from __future__ import annotations

import base64
import calendar
import io
import logging
import statistics
from collections import Counter
from datetime import datetime
from decimal import Decimal
from typing import Any

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.db.models import Count, F, Sum
from django.utils import timezone

from shop.models import ClientProfile, Order, OrderItem, Product

logger = logging.getLogger('shop')


def format_date_dd_mm_yyyy(dt: datetime | None, tz=None) -> str:
    """Format datetime as DD/MM/YYYY in given timezone."""
    if dt is None:
        return ''
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt, tz) if tz else timezone.localtime(dt)
    return dt.strftime('%d/%m/%Y')


def format_datetime_dd_mm_yyyy(dt: datetime | None, tz=None) -> str:
    """Format datetime as DD/MM/YYYY HH:MM."""
    if dt is None:
        return ''
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt, tz) if tz else timezone.localtime(dt)
    return dt.strftime('%d/%m/%Y %H:%M')


def text_calendar(year: int, month: int) -> str:
    return calendar.month(year, month)


def sales_statistics() -> dict[str, Any]:
    """Compute sales stats for dashboard."""
    order_totals = [float(order.items_total) for order in Order.objects.prefetch_related('items')]

    ages = [c.age for c in ClientProfile.objects.all()]

    category_qty = (
        OrderItem.objects.values('product__category__name')
        .annotate(qty=Count('id'))
        .order_by('-qty')
    )

    popular_category = category_qty[0]['product__category__name'] if category_qty else '—'

    profit_by_category = (
        OrderItem.objects.values('product__category__name')
        .annotate(profit=Sum(F('unit_price') * F('quantity')))
        .order_by('-profit')
    )
    top_profit_category = profit_by_category[0]['product__category__name'] if profit_by_category else '—'

    total_sales = Decimal('0')
    for order in Order.objects.prefetch_related('items'):
        total_sales += order.items_total

    stats: dict[str, Any] = {
        'order_totals': order_totals,
        'total_sales': total_sales,
        'clients_alpha': ClientProfile.objects.select_related('user').order_by(
            'user__last_name', 'user__first_name'
        ),
        'products_alpha': Product.objects.order_by('name'),
        'popular_category': popular_category,
        'top_profit_category': top_profit_category,
        'category_breakdown': list(category_qty),
    }

    if order_totals:
        stats['sales_mean'] = round(statistics.mean(order_totals), 2)
        stats['sales_median'] = round(statistics.median(order_totals), 2)
        try:
            stats['sales_mode'] = round(statistics.mode(order_totals), 2)
        except statistics.StatisticsError:
            stats['sales_mode'] = round(order_totals[0], 2)
    else:
        stats['sales_mean'] = stats['sales_median'] = stats['sales_mode'] = 0

    if ages:
        stats['age_mean'] = round(statistics.mean(ages), 1)
        stats['age_median'] = round(statistics.median(ages), 1)
    else:
        stats['age_mean'] = stats['age_median'] = 0

    return stats


def build_category_chart_base64() -> str:
    """Bar chart: order items count by product category."""
    data = (
        OrderItem.objects.values('product__category__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    if not data:
        return ''

    labels = [d['product__category__name'] for d in data]
    values = [d['count'] for d in data]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.pie(values, labels=labels, autopct='%1.1f%%')
    ax.set_title('Orders by product category')

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')
