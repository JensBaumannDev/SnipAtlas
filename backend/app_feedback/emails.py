"""Mails sent for requests."""

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from core.mail import mail_language

from .models import Suggestion

ANSWER_SUBJECTS = {
    'de': 'Antwort auf deine Anfrage bei SnipAtlas',
    'en': 'Reply to your SnipAtlas request',
}


def send_answer_mail(suggestion: Suggestion) -> None:
    """Send the answer in the language of the request if the sender wants mails."""
    recipient = suggestion.notify_email
    if not recipient:
        return
    language = mail_language(suggestion.language)
    template = f'app_feedback/emails/{language}/suggestion_answer.txt'
    body = render_to_string(template, {'suggestion': suggestion})
    subject = ANSWER_SUBJECTS[language]
    EmailMessage(subject, body, to=[recipient], reply_to=[settings.REPLY_TO_EMAIL]).send()
