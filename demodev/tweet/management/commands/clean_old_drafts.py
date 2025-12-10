from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tweet.models import TweetDraft


class Command(BaseCommand):
    help = 'Clean up old draft tweets that have not been updated'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete drafts older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options.get('days', 30)
        dry_run = options.get('dry_run', False)
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find all drafts older than cutoff date
        old_drafts = TweetDraft.objects.filter(updated_at__lt=cutoff_date)
        
        count = old_drafts.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} drafts older than {cutoff_date}'
                )
            )
            for draft in old_drafts[:10]:  # Show first 10
                self.stdout.write(
                    f'  - Draft {draft.id} by @{draft.user.username} '
                    f'(last updated: {draft.updated_at})'
                )
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            # Delete the drafts
            old_drafts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} old drafts (older than {days} days)'
                )
            )
