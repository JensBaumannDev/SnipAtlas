from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    status_code = 400
    default_detail = 'Email or password is wrong.'
    default_code = 'invalid_credentials'
