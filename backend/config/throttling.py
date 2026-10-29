from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class IpRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class AuthRateThrottle(IpRateThrottle):
    scope = 'auth'


class RequestRateThrottle(IpRateThrottle):
    scope = 'requests'
