from django import template

from shop.images import WIDTHS, variant_name

register = template.Library()


@register.simple_tag
def srcset(field_file):
    if not field_file:
        return ''
    storage = field_file.storage
    return ', '.join(f'{storage.url(variant_name(field_file.name, w))} {w}w' for w in WIDTHS)