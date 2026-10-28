from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class AuthRateThrottle(SimpleRateThrottle):
    scope = 'auth'

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
