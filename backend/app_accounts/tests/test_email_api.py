from smtplib import SMTPException
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core import mail
from django.core.mail import EmailMessage
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User
from app_accounts.tokens import ACTIVATION, EMAIL_CHANGE, check_link_token

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-email')


def change(client: APIClient, **changes: object) -> Response:
    data = {'email': 'ada.neu@example.com', 'password': PASSWORD} | changes
    return client.post(URL, data, format='json')


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def confirm_link(body: str) -> tuple[str, str]:
    link = next(word for word in body.split() if '/email-bestaetigen?' in word)
    query = parse_qs(urlsplit(link).query)
    return query['uid'][0], query['token'][0]


def stored_email(user: User) -> str:
    user.refresh_from_db()
    return user.email


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user('grace@example.com', PASSWORD)


# Change
def test_change_email_returns_user_with_current_address(logged_in: APIClient, user: User) -> None:
    response = change(logged_in)
    assert response.status_code == 200
    assert response.json() == {
        'email': 'ada@example.com',
        'since': user.since.isoformat(),
        'notifyByMail': True,
        'accent': 'blue',
    }


def test_change_email_keeps_address_until_confirmed(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    user.refresh_from_db()
    assert user.email == 'ada@example.com'
    assert user.pending_email == 'ada.neu@example.com'


def test_change_email_lowercases_and_trims(logged_in: APIClient, user: User) -> None:
    change(logged_in, email='  Ada.Neu@Example.COM ')
    user.refresh_from_db()
    assert user.pending_email == 'ada.neu@example.com'
    assert mail.outbox[0].to == ['ada.neu@example.com']


def test_change_email_sends_link_to_new_address_only(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ['ada.neu@example.com']
    assert message.from_email == 'noreply@snipatlas.jensbaumann.com'
    assert message.subject == 'Bestätige deine neue E-Mail-Adresse'
    assert message.content_subtype == 'plain'
    assert 'Der Link gilt 24 Stunden' in message.body


def test_change_email_link_is_valid(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    user.refresh_from_db()
    uid, token = confirm_link(mail.outbox[0].body)
    assert force_str(urlsafe_base64_decode(uid)) == str(user.pk)
    assert check_link_token(user, token, EMAIL_CHANGE)
    assert not check_link_token(user, token, ACTIVATION)


@override_settings(FRONTEND_URL='https://snipatlas.jensbaumann.com')
def test_change_email_link_uses_frontend_url(logged_in: APIClient) -> None:
    change(logged_in)
    assert 'https://snipatlas.jensbaumann.com/email-bestaetigen?uid=' in mail.outbox[0].body


def test_change_email_mail_follows_request_language(logged_in: APIClient) -> None:
    logged_in.post(
        URL,
        {'email': 'ada.neu@example.com', 'password': PASSWORD},
        format='json',
        HTTP_ACCEPT_LANGUAGE='en',
    )
    assert mail.outbox[0].subject == 'Confirm your new email address'
    assert 'The link is valid for 24 hours' in mail.outbox[0].body


def test_new_change_request_voids_old_link(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    change(logged_in, email='ada.other@example.com')
    user.refresh_from_db()
    (_, old), (_, new) = (confirm_link(message.body) for message in mail.outbox)
    assert user.pending_email == 'ada.other@example.com'
    assert not check_link_token(user, old, EMAIL_CHANGE)
    assert check_link_token(user, new, EMAIL_CHANGE)


def test_change_email_to_own_email_clears_pending_without_mail(
    logged_in: APIClient, user: User
) -> None:
    change(logged_in)
    mail.outbox.clear()
    response = change(logged_in, email='ADA@example.com')
    user.refresh_from_db()
    assert response.status_code == 200
    assert (user.email, user.pending_email) == ('ada@example.com', '')
    assert mail.outbox == []


def test_change_email_keeps_user_logged_in(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    assert logged_in.get(reverse('auth-me')).json()['email'] == 'ada@example.com'


def test_login_with_pending_email_fails(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    change(api_client)
    api_client.logout()
    new = {'email': 'ada.neu@example.com', 'password': PASSWORD}
    old = {'email': 'ada@example.com', 'password': PASSWORD}
    assert api_client.post(reverse('auth-login'), new, format='json').status_code == 400
    assert api_client.post(reverse('auth-login'), old, format='json').status_code == 200


def test_change_email_ignores_other_fields(logged_in: APIClient, user: User) -> None:
    change(logged_in, isStaff=True, accent='teal', notifyByMail=False, pendingEmail='x@y.de')
    user.refresh_from_db()
    assert (user.is_staff, user.accent, user.notify_by_mail) == (False, 'blue', True)
    assert user.pending_email == 'ada.neu@example.com'


def test_change_email_keeps_other_user(logged_in: APIClient, user: User, other_user: User) -> None:
    change(logged_in)
    other_user.refresh_from_db()
    assert (other_user.email, other_user.pending_email) == ('grace@example.com', '')


def test_change_email_keeps_password(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_change_email_with_failing_mail_still_answers(
    logged_in: APIClient, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: EmailMessage, fail_silently: bool = False) -> int:
        raise SMTPException

    monkeypatch.setattr(EmailMessage, 'send', fail)
    assert change(logged_in).status_code == 200


def test_failed_change_sets_no_pending_email_and_sends_no_mail(
    logged_in: APIClient, user: User
) -> None:
    change(logged_in, password='Falsches-Passwort-1')
    change(logged_in, email='no-mail')
    user.refresh_from_db()
    assert user.pending_email == ''
    assert mail.outbox == []


# Wrong password
@pytest.mark.parametrize('password', ['Falsches-Passwort-1', PASSWORD.lower(), f' {PASSWORD}'])
def test_change_email_with_wrong_password_is_rejected(
    logged_in: APIClient, user: User, password: str
) -> None:
    response = change(logged_in, password=password)
    assert response.status_code == 400
    assert response.json() == {'code': 'wrong_password'}
    assert stored_email(user) == 'ada@example.com'


@pytest.mark.parametrize('email', ['no-mail', 'grace@example.com', ''])
def test_wrong_password_is_reported_before_email_errors(
    logged_in: APIClient, other_user: User, email: str
) -> None:
    response = change(logged_in, email=email, password='Falsches-Passwort-1')
    assert response.json() == {'code': 'wrong_password'}


def test_change_email_of_user_without_password_is_rejected(api_client: APIClient, db: None) -> None:
    user = User.objects.create_user('nopass@example.com')
    api_client.force_login(user)
    assert change(api_client).json() == {'code': 'wrong_password'}


# Invalid fields
@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'email': ''}, {'email': ['blank']}),
        ({'email': '   '}, {'email': ['blank']}),
        ({'email': None}, {'email': ['null']}),
        ({'email': 'no-mail'}, {'email': ['invalid']}),
        ({'email': ['a@b.de']}, {'email': ['invalid']}),
        ({'email': f'{"a" * 250}@example.com'}, {'email': ['max_length']}),
        ({'email': 'grace@example.com'}, {'email': ['unique']}),
        ({'email': 'GRACE@example.com'}, {'email': ['unique']}),
        ({'password': ''}, {'password': ['blank']}),
        ({'password': None}, {'password': ['null']}),
    ],
)
def test_change_email_with_invalid_field_is_rejected(
    logged_in: APIClient, user: User, other_user: User, changes: dict, fields: dict
) -> None:
    assert field_errors(change(logged_in, **changes)) == fields
    assert stored_email(user) == 'ada@example.com'


def test_change_email_without_fields_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.post(URL, {}, format='json')
    assert field_errors(response) == {'password': ['required'], 'email': ['required']}


def test_change_email_with_list_body_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.post(URL, ['email'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}


# Security
def test_change_email_of_guest_is_rejected(api_client: APIClient, user: User) -> None:
    response = change(api_client)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert stored_email(user) == 'ada@example.com'


def test_change_email_with_unknown_session_is_rejected(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert change(api_client).status_code == 401


def test_change_email_of_deactivated_user_is_rejected(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert change(logged_in).status_code == 401
    assert stored_email(user) == 'ada@example.com'


def test_change_email_after_logout_is_rejected(logged_in: APIClient) -> None:
    logged_in.post(reverse('auth-logout'))
    assert change(logged_in).status_code == 401


def test_change_email_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    response = change(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert stored_email(user) == 'ada@example.com'


def test_change_email_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = {'email': 'ada.neu@example.com', 'password': PASSWORD}
    response = csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 200


def test_change_email_is_throttled_after_five_attempts(logged_in: APIClient, user: User) -> None:
    for _ in range(5):
        change(logged_in, password='Falsches-Passwort-1')
    response = change(logged_in)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert stored_email(user) == 'ada@example.com'


def test_change_email_shares_limit_with_login(logged_in: APIClient, user: User) -> None:
    login = {'email': 'ada@example.com', 'password': 'Falsches-Passwort-1'}
    for _ in range(5):
        logged_in.post(reverse('auth-login'), login, format='json')
    assert change(logged_in).status_code == 429


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_change_email_rejects_other_methods(logged_in: APIClient, user: User, method: str) -> None:
    response = getattr(logged_in, method)(URL, {'email': 'ada.neu@example.com'}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert stored_email(user) == 'ada@example.com'
