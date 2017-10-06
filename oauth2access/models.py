import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from oauthlib.oauth2 import OAuth2Token


class TokenField(models.TextField):
    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return OAuth2Token(json.loads(value))

    def to_python(self, value):
        if value is None:
            return None
        try:
            return OAuth2Token(json.loads(value))
        except (ValueError, TypeError):
            raise ValidationError("Invalid token")

    def get_prep_value(self, value):
        return json.dumps(value)


class ServiceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.CharField(max_length=127)
    token = TokenField()

    class Meta:
        unique_together = ('user', 'service')

    def __str__(self):
        return 'service=%s, user=%s' % (self.service, self.user)
