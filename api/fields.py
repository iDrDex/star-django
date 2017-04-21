from rest_framework import serializers

class S3Field(serializers.Field):
    def to_representation(self, obj):
        return obj.url
