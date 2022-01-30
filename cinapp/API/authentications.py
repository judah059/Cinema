import datetime
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone
from django.conf import settings
from rest_framework import exceptions


class TokenDeadAuthentication(TokenAuthentication):
    def get_model(self):
        if self.model is not None:
            return self.model
        from cinapp.models import CustomToken
        return CustomToken

    def authenticate(self, request):
        try:
            user, token = super(TokenDeadAuthentication, self).authenticate(request)
        except TypeError:
            return None
        if not user.is_superuser:
            delta = (datetime.datetime.now(timezone.utc) - token.last_action).seconds
            if delta > settings.TOKEN_TIME_TO_LIVE:
                token.delete()
                msg = 'Invalid token. Time for token is over.'
                raise exceptions.AuthenticationFailed(msg)
        token.last_action = datetime.datetime.now(timezone.utc)
        token.save()
        return user, token
