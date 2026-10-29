"""Command that deletes old done guest requests."""

from django.core.management.base import BaseCommand

from app_feedback.models import Suggestion


class Command(BaseCommand):
    """Delete done guest requests older than six months."""

    help = 'Delete done guest tickets older than six months.'

    def handle(self, *args: object, **options: object) -> None:
        """Delete the old requests and print how many were deleted."""
        count = Suggestion.delete_old_guest_tickets()
        self.stdout.write(f'Deleted {count} old guest tickets.')
