from django.db.models import QuerySet
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from config.throttling import RequestRateThrottle

from .serializers import KIND_SERIALIZERS, MyRequestSerializer, SuggestionSerializer


def sent_kind(data: object) -> object:
    return data.get('kind') if isinstance(data, dict) else None


def is_bot(data: object) -> bool:
    return isinstance(data, dict) and bool(data.get('website'))


class RequestCreateView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle, RequestRateThrottle)

    def get_serializer_class(self) -> type[SuggestionSerializer]:
        kind = sent_kind(self.request.data)
        if not isinstance(kind, str):
            return SuggestionSerializer
        return KIND_SERIALIZERS.get(kind, SuggestionSerializer)

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        if is_bot(request.data):
            return Response({'id': None}, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer: SuggestionSerializer) -> None:
        user = self.request.user
        serializer.save(user=user if user.is_authenticated else None)


class MyRequestListView(generics.ListAPIView):
    serializer_class = MyRequestSerializer

    def get_queryset(self) -> QuerySet:
        return self.request.user.suggestions.all()
