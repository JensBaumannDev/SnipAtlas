import re
from smtplib import SMTPException

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.mail import EmailMessage
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-password-reset')
LINK = re.compile(
    r'http://localhost:4200/passwort-zuruecksetzen\?uid=(?P<uid>[\w-]+)&token=(?P<token>[\w-]+)'
)


def request_reset(client: APIClient, email: object = 'ada@example.com') -> Response:
    return client.post(URL, {'email': email}, format='json')


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def link_parts(body: str) -> tuple[str, str]:
    match = LINK.search(body)
    assert match
    return match['uid'], match['token']


# Mail
def test_reset_for_known_email_sends_mail(api_client: APIClient, user: User) -> None:
    response = request_reset(api_client)
    assert response.status_code == 204
    assert response.content == b''
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ['ada@example.com']
    assert message.from_email == 'noreply@snipatlas.jensbaumann.com'
    assert message.subject == 'Neues Passwort für SnipAtlas'


def test_reset_mail_contains_valid_link(api_client: APIClient, user: User) -> None:
    request_reset(api_client)
    uid, token = link_parts(mail.outbox[0].body)
    assert force_str(urlsafe_base64_decode(uid)) == str(user.pk)
    assert default_token_generator.check_token(user, token)


def test_reset_mail_is_plain_text(api_client: APIClient, user: User) -> None:
    request_reset(api_client)
    message = mail.outbox[0]
    assert message.content_subtype == 'plain'
    assert '&amp;' not in message.body
    assert '<' not in message.body


@override_settings(FRONTEND_URL='https://snipatlas.jensbaumann.com')
def test_reset_link_uses_frontend_url(api_client: APIClient, user: User) -> None:
    request_reset(api_client)
    assert 'https://snipatlas.jensbaumann.com/passwort-zuruecksetzen?uid=' in mail.outbox[0].body


def test_reset_mail_goes_to_stored_address(api_client: APIClient, user: User) -> None:
    request_reset(api_client, ' ADA@Example.COM ')
    assert mail.outbox[0].to == ['ada@example.com']


def test_reset_mail_goes_only_to_matching_user(api_client: APIClient, user: User) -> None:
    User.objects.create_user('grace@example.com', PASSWORD)
    request_reset(api_client)
    assert [message.to for message in mail.outbox] == [['ada@example.com']]


def test_reset_with_unicode_lookalike_sends_no_mail(api_client: APIClient, db: None) -> None:
    User.objects.create_user('tim@example.com', PASSWORD)
    for lookalike in ['tım@example.com', 'TİM@example.com']:
        request_reset(api_client, lookalike)
    assert mail.outbox == []


def test_reset_keeps_password(api_client: APIClient, user: User) -> None:
    request_reset(api_client)
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_reset_does_not_log_in(api_client: APIClient, user: User) -> None:
    request_reset(api_client)
    assert api_client.get(reverse('auth-me')).status_code == 401


def test_reset_of_logged_in_user_is_allowed(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    assert request_reset(api_client).status_code == 204
    assert len(mail.outbox) == 1


# Same answer
def test_reset_for_unknown_email_answers_the_same(api_client: APIClient, user: User) -> None:
    known = request_reset(api_client)
    unknown = request_reset(api_client, 'unknown@example.com')
    assert (unknown.status_code, unknown.content) == (known.status_code, known.content)
    assert len(mail.outbox) == 1


def test_reset_for_deactivated_user_sends_no_mail(api_client: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert request_reset(api_client).status_code == 204
    assert mail.outbox == []


def test_reset_for_user_without_password_sends_no_mail(api_client: APIClient, db: None) -> None:
    User.objects.create_user('nopass@example.com')
    assert request_reset(api_client, 'nopass@example.com').status_code == 204
    assert mail.outbox == []


def test_reset_with_failing_mail_answers_the_same(
    api_client: APIClient, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: EmailMessage, fail_silently: bool = False) -> int:
        raise SMTPException

    monkeypatch.setattr(EmailMessage, 'send', fail)
    response = request_reset(api_client)
    assert response.status_code == 204
    assert response.content == b''


# Invalid fields
@pytest.mark.parametrize(
    ('email', 'code'),
    [
        ('', 'blank'),
        (None, 'null'),
        ('ada', 'invalid'),
        ('ada@', 'invalid'),
        ('ada@example.com\x00', 'null_characters_not_allowed'),
        (f'{"a" * 243}@example.com', 'max_length'),
    ],
)
def test_reset_with_invalid_email_is_rejected(
    api_client: APIClient, user: User, email: object, code: str
) -> None:
    assert code in field_errors(request_reset(api_client, email))['email']
    assert mail.outbox == []


def test_reset_without_email_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, {}, format='json')
    assert field_errors(response) == {'email': ['required']}


def test_reset_with_list_body_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, ['email'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}


def test_reset_ignores_other_fields(api_client: APIClient, user: User) -> None:
    data = {'email': 'ada@example.com', 'to': 'evil@example.com', 'user': 999}
    api_client.post(URL, data, format='json')
    assert mail.outbox[0].to == ['ada@example.com']


# Security
def test_reset_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    response = request_reset(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert mail.outbox == []


def test_reset_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = {'email': 'ada@example.com'}
    response = csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 204


def test_reset_with_unknown_session_is_allowed(api_client: APIClient, user: User) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert request_reset(api_client).status_code == 204


def test_reset_is_throttled_after_three_attempts(api_client: APIClient, user: User) -> None:
    for email in ['unknown@example.com', 'ada', 'ada@example.com']:
        request_reset(api_client, email)
    response = request_reset(api_client)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert len(mail.outbox) == 1


def test_reset_limit_is_separate_from_login(api_client: APIClient, user: User) -> None:
    login = {'email': 'ada@example.com', 'password': 'Falsches-Passwort-1'}
    for _ in range(5):
        api_client.post(reverse('auth-login'), login, format='json')
    assert request_reset(api_client).status_code == 204


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_reset_rejects_other_methods(api_client: APIClient, user: User, method: str) -> None:
    response = getattr(api_client, method)(URL, {'email': 'ada@example.com'}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert mail.outbox == []
