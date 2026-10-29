import logging
from smtplib import SMTPException
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User

logger = logging.getLogger(__name__)

RESET_SUBJECT = 'Neues Passwort für SnipAtlas'
RESET_PATH = '/passwort-zuruecksetzen'


def reset_link(user: User) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    query = urlencode({'uid': uid, 'token': default_token_generator.make_token(user)})
    return f'{settings.FRONTEND_URL}{RESET_PATH}?{query}'


def send_reset_mail(user: User) -> None:
    body = render_to_string('emails/password_reset.txt', {'link': reset_link(user)})
    try:
        EmailMessage(RESET_SUBJECT, body, to=[user.email]).send()
    except SMTPException, OSError:
        logger.exception('Password reset mail failed')
