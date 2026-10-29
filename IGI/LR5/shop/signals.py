from django.db import models, transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from shop.images import WIDTHS, variant_name


def _file_fields(model):
    return [f for f in model._meta.concrete_fields if isinstance(f, models.FileField)]


def _delete_later(model, field_name, file):
    """Delete the file (and its resized copies) from the bucket once the DB transaction commits."""
    storage, name = file.storage, file.name
    with_variants = field_name in getattr(model, 'responsive_fields', ())

    def _do():
        storage.delete(name)
        if with_variants:
            for w in WIDTHS:
                storage.delete(variant_name(name, w))

    transaction.on_commit(_do)


@receiver(post_delete)
def delete_files_on_delete(sender, instance, **kwargs):
    if sender._meta.app_label != 'shop':
        return
    for field in _file_fields(sender):
        file = getattr(instance, field.name)
        if file:
            _delete_later(sender, field.name, file)


@receiver(pre_save)
def delete_old_file_on_change(sender, instance, **kwargs):
    if sender._meta.app_label != 'shop' or kwargs.get('raw') or not instance.pk:
        return
    fields = _file_fields(sender)
    if not fields:
        return
    old = sender.objects.filter(pk=instance.pk).first()
    if old is None:
        return
    for field in fields:
        old_file = getattr(old, field.name)
        new_file = getattr(instance, field.name)
        if old_file and old_file.name != (new_file.name or ''):
            _delete_later(sender, field.name, old_file)