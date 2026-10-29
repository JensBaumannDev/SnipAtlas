from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .models import Suggestion

ANSWER_SUBJECT = 'Antwort auf deine Anfrage bei SnipAtlas'


def send_answer_mail(suggestion: Suggestion) -> None:
    recipient = suggestion.notify_email
    if not recipient:
        return
    body = render_to_string('app_feedback/emails/suggestion_answer.txt', {'suggestion': suggestion})
    message = EmailMessage(ANSWER_SUBJECT, body, to=[recipient], reply_to=[settings.REPLY_TO_EMAIL])
    message.send()
