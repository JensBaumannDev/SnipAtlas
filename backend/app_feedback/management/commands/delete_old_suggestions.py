from django.core.management.base import BaseCommand

from app_feedback.models import Suggestion


class Command(BaseCommand):
    help = 'Delete done guest tickets older than six months.'

    def handle(self, *args: object, **options: object) -> None:
        count = Suggestion.delete_old_guest_tickets()
        self.stdout.write(f'Deleted {count} old guest tickets.')
