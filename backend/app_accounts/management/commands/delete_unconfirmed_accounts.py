"""Command that deletes accounts whose email was never confirmed."""

from django.core.management.base import BaseCommand

from app_accounts.models import User


class Command(BaseCommand):
    """Delete unconfirmed accounts older than seven days."""

    help = 'Delete accounts whose email was not confirmed within seven days.'

    def handle(self, *args: object, **options: object) -> None:
        """Delete the accounts and print how many were deleted."""
        count = User.delete_unconfirmed()
        self.stdout.write(f'Deleted {count} unconfirmed accounts.')
