import base64

from rest_framework import serializers
from django.core.files.base import ContentFile


class Base64ImageField(serializers.ImageField):
    """
    Поле изображения, которое принимает закодированную
    в Base64 строку изображения.
    Преобразует строку Base64 в объект ContentFile и
    сохраняет его в поле изображения.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, value):
        if value:
            return value.url
        return None
