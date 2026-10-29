from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    status_code = 400
    default_detail = 'Email or password is wrong.'
    default_code = 'invalid_credentials'


class InvalidLink(APIException):
    status_code = 400
    default_detail = 'The link is invalid or expired.'
    default_code = 'invalid_link'


class WrongPassword(APIException):
    status_code = 400
    default_detail = 'The current password is wrong.'
    default_code = 'wrong_password'
