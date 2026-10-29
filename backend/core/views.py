from typing import NoReturn

from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView


class ApiNotFoundView(APIView):
    permission_classes = [AllowAny]

    def http_method_not_allowed(
        self, request: Request, *args: object, **kwargs: object
    ) -> NoReturn:
        raise NotFound

    options = http_method_not_allowed
