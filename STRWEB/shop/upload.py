import os
import uuid

from django.utils.deconstruct import deconstructible


@deconstructible
class UploadPath:
    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        ext = os.path.splitext(filename)[1].lower()
        return f'{self.folder}/{uuid.uuid4().hex}{ext}'