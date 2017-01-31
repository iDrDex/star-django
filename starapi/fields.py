from s3field.ops import generate_url
from rest_framework import serializers

class S3Field(serializers.Field):
    def to_representation(self, obj):
        return generate_url(obj)
