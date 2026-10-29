import io
import os

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

WIDTHS = (480, 800, 1200)


def variant_name(name, width):
    """articles/abc.jpg -> articles/abc_480.webp"""
    base, _ = os.path.splitext(name)
    return f'{base}_{width}.webp'


def make_variants(field_file, data, widths=WIDTHS):
    """Save resized WebP copies of the image next to the original (same storage)."""
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    except Exception:
        return  # not a readable image
    img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
    for w in widths:
        target_w = min(w, img.width)  # never upscale
        target_h = round(img.height * target_w / img.width)
        buf = io.BytesIO()
        img.resize((target_w, target_h), Image.LANCZOS).save(buf, 'WEBP', quality=80)
        field_file.storage.save(variant_name(field_file.name, w), ContentFile(buf.getvalue()))