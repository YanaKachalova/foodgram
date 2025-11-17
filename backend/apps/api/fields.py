import base64
import uuid
import imghdr
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, image_data):
        if isinstance(image_data, str) and image_data.startswith("data:image"):
            header, b64 = image_data.split(";base64,")
            file_data = base64.b64decode(b64)
            ext = imghdr.what(None, h=file_data) or "jpg"
            image_uuid = uuid.uuid4()
            file_name = f"{image_uuid}.{ext}"
            image_data = ContentFile(file_data, name=file_name)

        return super().to_internal_value(image_data)
