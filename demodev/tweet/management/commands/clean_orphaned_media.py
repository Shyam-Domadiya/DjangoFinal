from django.core.management.base import BaseCommand
from django.db.models import Q
from tweet.models import Media, Tweet, TweetDraft


class Command(BaseCommand):
    help = 'Clean up orphaned media files that are not associated with any tweet or draft'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Find all media files
        all_media = Media.objects.all()
        
        # Find media that is not associated with any tweet or draft
        orphaned_media = []
        
        for media in all_media:
            # Check if media is associated with any tweet
            tweet_count = Tweet.objects.filter(media=media).count()
            # Check if media is associated with any draft
            draft_count = TweetDraft.objects.filter(media=media).count()
            
            # If not associated with any tweet or draft, it's orphaned
            if tweet_count == 0 and draft_count == 0:
                orphaned_media.append(media)
        
        count = len(orphaned_media)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} orphaned media files'
                )
            )
            for media in orphaned_media[:10]:  # Show first 10
                self.stdout.write(
                    f'  - Media {media.id} by @{media.user.username} '
                    f'(uploaded: {media.uploaded_at})'
                )
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            # Delete the orphaned media files
            for media in orphaned_media:
                # Delete the media files from storage
                media.delete_file()
                # Delete the media object from database
                media.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} orphaned media files'
                )
            )
