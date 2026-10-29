"""Shared error format for all API responses."""

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler, set_rollback

logger = logging.getLogger(__name__)


def api_exception_handler(exc: Exception, context: dict) -> Response:
    """Turn any exception into a response in the shared error format."""
    response = exception_handler(exc, context)
    if response is None:
        return server_error(exc)
    response.data = error_body(as_api_exception(exc))
    return response


def as_api_exception(exc: Exception) -> exceptions.APIException:
    """Convert Django's 404 and 403 errors into their DRF counterparts."""
    if isinstance(exc, Http404):
        return exceptions.NotFound()
    if isinstance(exc, PermissionDenied):
        return exceptions.PermissionDenied()
    return exc


def error_body(exc: exceptions.APIException) -> dict:
    """Build the error body with a code and field codes or a retry time."""
    if isinstance(exc, exceptions.ValidationError):
        return {'code': 'validation_error', 'fields': field_codes(exc)}
    body = {'code': exc.get_codes()}
    if isinstance(exc, exceptions.Throttled) and exc.wait is not None:
        body['retry_after'] = exc.wait
    return body


def field_codes(exc: exceptions.ValidationError) -> dict:
    """Return the error codes of a validation error grouped by field."""
    codes = exc.get_codes()
    if isinstance(codes, dict):
        return codes
    return {api_settings.NON_FIELD_ERRORS_KEY: codes}


def server_error(exc: Exception) -> Response:
    """Log an unhandled error and answer with a plain 500 response."""
    logger.error('Unhandled API error', exc_info=exc)
    set_rollback()
    return Response({'code': 'server_error'}, status=500)
