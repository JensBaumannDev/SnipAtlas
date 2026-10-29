import pytest
from django.forms.models import model_to_dict
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User
from app_content.models import Topic
from app_feedback.models import Suggestion

pytestmark = pytest.mark.django_db

CSRF_TOKEN = 'a' * 32
URL = reverse('request-create')
REASON = 'Ich verstehe interaktives Rebasen nicht.'
IDEA = 'Eine Suche über alle Bereiche, die auch Aliase findet.'
PROBLEM = 'Im zweiten Schritt fehlt ein Buchstabe.'


def entry_data(**changes: object) -> dict:
    data = {
        'kind': 'entry',
        'area': 'command',
        'topic': 'python',
        'title': 'git rebase -i erklären',
        'reason': REASON,
        'example': 'git rebase -i HEAD~3',
        'source': 'https://git-scm.com/docs/git-rebase',
        'email': 'guest@example.com',
    }
    return data | changes


def improvement_data(**changes: object) -> dict:
    data = {
        'kind': 'improvement',
        'area': 'feature',
        'idea': IDEA,
        'benefit': 'Schneller finden',
        'email': 'guest@example.com',
    }
    return data | changes


def bug_data(**changes: object) -> dict:
    data = {
        'kind': 'bug',
        'type': 'broken',
        'location': 'Virtuelle Umgebung anlegen',
        'problem': PROBLEM,
        'correction': 'python -m venv .venv',
        'environment': 'Windows 11',
        'email': 'guest@example.com',
    }
    return data | changes


def send(client: APIClient, data: object, **extra: str) -> Response:
    return client.post(URL, data, format='json', **extra)


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def stored() -> dict:
    return model_to_dict(Suggestion.objects.get(), exclude=('id',))


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture(autouse=True)
def topic_exists(topic: Topic) -> Topic:
    return topic


# Create
def test_guest_sends_entry_request(api_client: APIClient, topic: Topic) -> None:
    response = send(api_client, entry_data())
    suggestion = Suggestion.objects.get()
    assert response.status_code == 201
    assert response.json() == {'id': suggestion.pk}
    assert stored() | {'answered_at': None} == {
        'kind': 'entry',
        'user': None,
        'email': 'guest@example.com',
        'status': 'open',
        'answer': '',
        'answered_at': None,
        'area': 'command',
        'topic': topic.pk,
        'title': 'git rebase -i erklären',
        'reason': REASON,
        'example': 'git rebase -i HEAD~3',
        'source': 'https://git-scm.com/docs/git-rebase',
        'idea': '',
        'benefit': '',
        'bug_type': '',
        'location': '',
        'problem': '',
        'correction': '',
        'environment': '',
    }


def test_guest_sends_improvement_request(api_client: APIClient) -> None:
    assert send(api_client, improvement_data()).status_code == 201
    suggestion = Suggestion.objects.get()
    assert (suggestion.kind, suggestion.area) == ('improvement', 'feature')
    assert (suggestion.idea, suggestion.benefit) == (IDEA, 'Schneller finden')
    assert suggestion.topic is None


def test_guest_sends_bug_request(api_client: APIClient) -> None:
    assert send(api_client, bug_data()).status_code == 201
    suggestion = Suggestion.objects.get()
    assert (suggestion.kind, suggestion.bug_type) == ('bug', 'broken')
    assert suggestion.location == 'Virtuelle Umgebung anlegen'
    assert suggestion.problem == PROBLEM
    assert suggestion.correction == 'python -m venv .venv'
    assert suggestion.environment == 'Windows 11'
    assert suggestion.area == ''


@pytest.mark.parametrize('data', [entry_data, improvement_data, bug_data])
def test_user_sends_request_without_email(logged_in: APIClient, user: User, data: object) -> None:
    body = data()
    del body['email']
    assert send(logged_in, body).status_code == 201
    suggestion = Suggestion.objects.get()
    assert suggestion.user == user
    assert suggestion.email == ''
    assert suggestion.contact_email == 'ada@example.com'


def test_user_request_ignores_given_email(logged_in: APIClient, user: User) -> None:
    send(logged_in, improvement_data(email='other@example.com'))
    assert Suggestion.objects.get().email == ''


def test_user_request_ignores_invalid_email(logged_in: APIClient) -> None:
    assert send(logged_in, improvement_data(email='no-mail')).status_code == 201


@pytest.mark.parametrize(
    ('data', 'optional'),
    [
        (entry_data, ('example', 'source')),
        (improvement_data, ('benefit',)),
        (bug_data, ('correction', 'environment')),
    ],
)
def test_request_without_optional_fields_is_stored(
    api_client: APIClient, data: object, optional: tuple[str, ...]
) -> None:
    body = data()
    for field in optional:
        del body[field]
    assert send(api_client, body).status_code == 201
    assert all(stored()[field] == '' for field in optional)


def test_request_accepts_empty_optional_fields(api_client: APIClient) -> None:
    assert send(api_client, entry_data(example='', source='')).status_code == 201


def test_request_trims_whitespace(api_client: APIClient) -> None:
    send(api_client, entry_data(title='  git rebase  ', email=' guest@example.com '))
    assert stored()['title'] == 'git rebase'
    assert stored()['email'] == 'guest@example.com'


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('title', 'x' * 120),
        ('reason', 'x' * 20),
        ('reason', 'x' * 1000),
        ('example', 'x' * 2000),
        ('source', 'http://example.com/' + 'x' * 281),
    ],
)
def test_request_accepts_values_at_the_limit(api_client: APIClient, field: str, value: str) -> None:
    assert send(api_client, entry_data(**{field: value})).status_code == 201


def test_request_ignores_fields_of_other_kinds(api_client: APIClient) -> None:
    send(api_client, entry_data(idea=IDEA, type='typo', location='Seite', problem=PROBLEM))
    assert (stored()['idea'], stored()['bug_type'], stored()['location']) == ('', '', '')


def test_request_ignores_internal_fields(api_client: APIClient, user: User) -> None:
    body = entry_data(
        status='done', answer='Erledigt', answeredAt='2026-01-01T00:00:00Z', user=user.pk, id=99
    )
    response = send(api_client, body)
    suggestion = Suggestion.objects.get()
    assert response.json() == {'id': suggestion.pk}
    assert suggestion.pk != 99
    assert (suggestion.status, suggestion.answer, suggestion.user) == ('open', '', None)
    assert suggestion.answered_at is None


def test_request_keeps_html_as_text(api_client: APIClient) -> None:
    send(api_client, entry_data(title='<script>alert(1)</script>'))
    assert stored()['title'] == '<script>alert(1)</script>'


def test_request_ignores_query_parameters(api_client: APIClient) -> None:
    response = api_client.post(f'{URL}?kind=bug&status=done', entry_data(), format='json')
    assert response.status_code == 201
    assert (stored()['kind'], stored()['status']) == ('entry', 'open')


def test_request_accepts_snake_case_type(api_client: APIClient) -> None:
    assert send(api_client, bug_data(type='typo')).status_code == 201
    assert stored()['bug_type'] == 'typo'


def test_request_queries(
    api_client: APIClient, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(2):
        send(api_client, entry_data())


# Honeypot
def test_filled_honeypot_stores_nothing(api_client: APIClient) -> None:
    response = send(api_client, entry_data(website='https://spam.example.com'))
    assert response.status_code == 201
    assert response.json() == {'id': None}
    assert not Suggestion.objects.exists()


def test_filled_honeypot_skips_validation(api_client: APIClient) -> None:
    response = send(api_client, {'kind': 'spam', 'website': 'x'})
    assert response.status_code == 201
    assert not Suggestion.objects.exists()


def test_filled_honeypot_of_user_stores_nothing(logged_in: APIClient) -> None:
    assert send(logged_in, improvement_data(website='x')).status_code == 201
    assert not Suggestion.objects.exists()


@pytest.mark.parametrize('website', ['', None])
def test_empty_honeypot_stores_request(api_client: APIClient, website: str | None) -> None:
    assert send(api_client, entry_data(website=website)).status_code == 201
    assert Suggestion.objects.count() == 1


# Invalid kind and body
def test_request_without_kind_is_rejected(api_client: APIClient) -> None:
    body = entry_data()
    del body['kind']
    assert field_errors(send(api_client, body)) == {'kind': ['required']}


@pytest.mark.parametrize(
    ('kind', 'code'),
    [
        ('question', 'invalid_choice'),
        ('ENTRY', 'invalid_choice'),
        ('', 'invalid_choice'),
        (None, 'null'),
        (['entry'], 'invalid_choice'),
        ({'entry': 1}, 'invalid_choice'),
        (1, 'invalid_choice'),
    ],
)
def test_request_with_invalid_kind_is_rejected(
    api_client: APIClient, kind: object, code: str
) -> None:
    assert field_errors(send(api_client, entry_data(kind=kind))) == {'kind': [code]}
    assert not Suggestion.objects.exists()


def test_request_with_list_body_is_rejected(api_client: APIClient) -> None:
    assert field_errors(send(api_client, [entry_data()])) == {'nonField': ['invalid']}


def test_request_with_broken_json_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, '{"kind":', content_type='application/json')
    assert response.status_code == 400
    assert response.json() == {'code': 'parse_error'}


def test_request_with_empty_body_is_rejected(api_client: APIClient) -> None:
    assert field_errors(send(api_client, {})) == {'kind': ['required'], 'email': ['required']}


# Invalid fields
@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'area': 'feature'}, {'area': ['invalid_choice']}),
        ({'area': ''}, {'area': ['invalid_choice']}),
        ({'area': None}, {'area': ['null']}),
        ({'topic': 'cobol'}, {'topic': ['does_not_exist']}),
        ({'topic': ''}, {'topic': ['null']}),
        ({'topic': None}, {'topic': ['null']}),
        ({'title': ''}, {'title': ['blank']}),
        ({'title': '   '}, {'title': ['blank']}),
        ({'title': 'x' * 121}, {'title': ['max_length']}),
        ({'reason': 'x' * 19}, {'reason': ['min_length']}),
        ({'reason': 'x' * 1001}, {'reason': ['max_length']}),
        ({'example': 'x' * 2001}, {'example': ['max_length']}),
        ({'source': 'example.com'}, {'source': ['invalid']}),
        ({'source': 'ftp://example.com/file'}, {'source': ['invalid']}),
        ({'source': 'javascript:alert(1)'}, {'source': ['invalid']}),
        ({'source': 'https://example.com/' + 'x' * 281}, {'source': ['max_length']}),
        ({'email': ''}, {'email': ['blank']}),
        ({'email': None}, {'email': ['null']}),
        ({'email': 'no-mail'}, {'email': ['invalid']}),
        ({'email': f'{"a" * 250}@example.com'}, {'email': ['max_length']}),
        (
            {'title': '', 'reason': 'kurz', 'email': 'no-mail'},
            {'title': ['blank'], 'reason': ['min_length'], 'email': ['invalid']},
        ),
    ],
)
def test_entry_request_with_invalid_field_is_rejected(
    api_client: APIClient, changes: dict, fields: dict
) -> None:
    assert field_errors(send(api_client, entry_data(**changes))) == fields
    assert not Suggestion.objects.exists()


@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'area': 'command'}, {'area': ['invalid_choice']}),
        ({'idea': ''}, {'idea': ['blank']}),
        ({'idea': 'x' * 19}, {'idea': ['min_length']}),
        ({'idea': 'x' * 2001}, {'idea': ['max_length']}),
        ({'benefit': 'x' * 1001}, {'benefit': ['max_length']}),
    ],
)
def test_improvement_request_with_invalid_field_is_rejected(
    api_client: APIClient, changes: dict, fields: dict
) -> None:
    assert field_errors(send(api_client, improvement_data(**changes))) == fields


@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'type': 'ugly'}, {'type': ['invalid_choice']}),
        ({'type': ''}, {'type': ['invalid_choice']}),
        ({'location': ''}, {'location': ['blank']}),
        ({'location': 'x' * 201}, {'location': ['max_length']}),
        ({'problem': 'x' * 19}, {'problem': ['min_length']}),
        ({'problem': 'x' * 2001}, {'problem': ['max_length']}),
        ({'correction': 'x' * 1001}, {'correction': ['max_length']}),
        ({'environment': 'x' * 201}, {'environment': ['max_length']}),
    ],
)
def test_bug_request_with_invalid_field_is_rejected(
    api_client: APIClient, changes: dict, fields: dict
) -> None:
    assert field_errors(send(api_client, bug_data(**changes))) == fields


@pytest.mark.parametrize(
    ('data', 'required'),
    [
        (entry_data, ('area', 'topic', 'title', 'reason', 'email')),
        (improvement_data, ('area', 'idea', 'email')),
        (bug_data, ('type', 'location', 'problem', 'email')),
    ],
)
def test_request_without_required_fields_is_rejected(
    api_client: APIClient, data: object, required: tuple[str, ...]
) -> None:
    body = {'kind': data()['kind']}
    assert field_errors(send(api_client, body)) == {field: ['required'] for field in required}


# Security
def test_guest_request_needs_no_csrf_token(csrf_client: APIClient) -> None:
    assert send(csrf_client, entry_data()).status_code == 201


def test_user_request_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    response = send(csrf_client, improvement_data())
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert not Suggestion.objects.exists()


def test_user_request_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    response = send(csrf_client, improvement_data(), HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 201


def test_request_with_unknown_session_is_stored_as_guest(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert send(api_client, improvement_data()).status_code == 201
    assert stored()['user'] is None


def test_request_of_deactivated_user_is_stored_as_guest(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    response = send(logged_in, improvement_data(email=''))
    assert field_errors(response) == {'email': ['blank']}
    assert send(logged_in, improvement_data()).status_code == 201
    assert stored()['user'] is None


def test_requests_are_throttled_per_ip(api_client: APIClient) -> None:
    for _ in range(5):
        assert send(api_client, improvement_data()).status_code == 201
    response = send(api_client, improvement_data())
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert Suggestion.objects.count() == 5


def test_throttle_counts_invalid_requests(api_client: APIClient) -> None:
    for _ in range(5):
        send(api_client, {})
    assert send(api_client, improvement_data()).status_code == 429


def test_throttle_counts_users_by_ip(logged_in: APIClient, api_client: APIClient) -> None:
    for _ in range(5):
        send(logged_in, improvement_data())
    logged_in.logout()
    assert send(api_client, improvement_data()).status_code == 429


def test_throttle_keeps_other_ips_apart(api_client: APIClient) -> None:
    for _ in range(5):
        send(api_client, improvement_data(), REMOTE_ADDR='10.0.0.1')
    assert send(api_client, improvement_data(), REMOTE_ADDR='10.0.0.2').status_code == 201


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_requests_reject_other_methods(
    api_client: APIClient, entry_suggestion: Suggestion, method: str
) -> None:
    before = model_to_dict(entry_suggestion)
    response = getattr(api_client, method)(URL, improvement_data(), format='json')
    entry_suggestion.refresh_from_db()
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert model_to_dict(entry_suggestion) == before
    assert Suggestion.objects.count() == 1
