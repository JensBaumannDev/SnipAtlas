"""API errors of the accounts app."""

from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    """Error for a wrong email address or password at login."""

    status_code = 400
    default_detail = 'Email or password is wrong.'
    default_code = 'invalid_credentials'


class InvalidLink(APIException):
    """Error for an invalid or expired password reset link."""

    status_code = 400
    default_detail = 'The link is invalid or expired.'
    default_code = 'invalid_link'


class NotActivated(APIException):
    """Error for a correct login of an account whose email is not confirmed yet."""

    status_code = 400
    default_detail = 'The email address is not confirmed yet.'
    default_code = 'not_activated'


class WrongPassword(APIException):
    """Error for a wrong current password."""

    status_code = 400
    default_detail = 'The current password is wrong.'
    default_code = 'wrong_password'
