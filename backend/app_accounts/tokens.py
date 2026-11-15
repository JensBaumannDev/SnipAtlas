"""Signed one-time tokens for the activation and email change links."""

from django.core.signing import BadSignature, TimestampSigner
from django.utils.crypto import constant_time_compare, salted_hmac

from .models import User

ACTIVATION = 'activation'
EMAIL_CHANGE = 'email-change'
LINK_MAX_AGE = 60 * 60 * 24


def make_link_token(user: User, purpose: str) -> str:
    """Return a token for the user that is valid for one day and one use."""
    return _signer(purpose).sign(_user_state(user, purpose))


def check_link_token(user: User, token: str, purpose: str) -> bool:
    """Return whether the token is valid for the user in their current state."""
    try:
        state = _signer(purpose).unsign(token, max_age=LINK_MAX_AGE)
    except BadSignature:
        return False
    return constant_time_compare(state, _user_state(user, purpose))


def _signer(purpose: str) -> TimestampSigner:
    """Return the signer for one kind of link."""
    return TimestampSigner(salt=f'app_accounts.{purpose}')


def _user_state(user: User, purpose: str) -> str:
    """Return a hash of the user data that changes once the link was used."""
    state = f'{user.pk}{user.password}{user.email}{user.email_confirmed}{user.pending_email}'
    return salted_hmac(purpose, state, algorithm='sha256').hexdigest()[::2]
