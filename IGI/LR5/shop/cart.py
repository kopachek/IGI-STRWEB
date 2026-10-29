from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from shop.models import Product

MAX_QTY = Decimal('100')
SESSION_KEY = 'cart'


def quantity_hint(product):
    if product.is_countable:
        return 'Enter a whole number from 1 to 100.'
    return f'Enter a quantity from {product.qty_min} to 100 ({product.get_unit_display().lower()}).'


def clean_quantity(product, value):
    """Parse user input into a valid Decimal for the product's unit, or return None."""
    try:
        qty = Decimal(str(value).strip().replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None
    if not qty.is_finite():
        return None
    if product.is_countable:
        if qty != qty.to_integral_value():
            return None
        qty = qty.to_integral_value()
    else:
        qty = qty.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    if qty < product.qty_min or qty > MAX_QTY:
        return None
    return qty


class Cart:
    """Session cart: {product_id(str): quantity(str, e.g. '2' or '1.5')}."""

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(SESSION_KEY, {})

    def _save(self):
        self.session.modified = True

    def _store(self, key, qty):
        # session is JSON, so the quantity is kept as a string
        self.data[key] = format(qty.quantize(Decimal('0.001')).normalize(), 'f')
        self._save()

    def add(self, product, quantity):
        key = str(product.pk)
        current = Decimal(str(self.data.get(key, 0)))
        self._store(key, min(current + quantity, MAX_QTY))

    def change(self, product, direction):
        """direction: +1 or -1, moves by the product's step."""
        key = str(product.pk)
        if key not in self.data:
            return
        new_qty = Decimal(str(self.data[key])) + product.qty_step * direction
        if new_qty < product.qty_min:
            del self.data[key]
            self._save()
        else:
            self._store(key, min(new_qty, MAX_QTY))

    def remove(self, product_id):
        if self.data.pop(str(product_id), None) is not None:
            self._save()

    def clear(self):
        self.data.clear()
        self._save()

    def items(self):
        """List of dicts: product, quantity (Decimal), line_total. Drops deleted/unavailable products."""
        products = Product.objects.filter(pk__in=list(self.data.keys()), is_available=True).order_by('name')
        result, found = [], set()
        for p in products:
            qty = Decimal(str(self.data[str(p.pk)]))
            line_total = (p.price * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            result.append({'product': p, 'quantity': qty, 'line_total': line_total})
            found.add(str(p.pk))
        stale = [k for k in self.data if k not in found]
        for k in stale:
            del self.data[k]
        if stale:
            self._save()
        return result


def cart_total(items):
    return sum((i['line_total'] for i in items), Decimal('0.00'))