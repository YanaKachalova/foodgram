import base64
import uuid
import imghdr
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            header, b64 = data.split(";base64,")
            file_data = base64.b64decode(b64)
            ext = imghdr.what(None, h=file_data) or "jpg"
            file_name = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(file_data, name=file_name)

        return super().to_internal_value(data)
