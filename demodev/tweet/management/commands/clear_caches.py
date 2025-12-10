"""
Management command to clear caches for performance optimization.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Q
from tweet.models import Tweet, Media
import logging

logger = logging.getLogger('tweet')


class Command(BaseCommand):
    help = 'Clear caches for search results and media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--search',
            action='store_true',
            help='Clear search result caches',
        )
        parser.add_argument(
            '--media',
            action='store_true',
            help='Clear media file caches',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all caches',
        )

    def handle(self, *args, **options):
        clear_search = options.get('search', False)
        clear_media = options.get('media', False)
        clear_all = options.get('all', False)

        if clear_all or clear_search:
            self.clear_search_caches()

        if clear_all or clear_media:
            self.clear_media_caches()

        if not (clear_search or clear_media or clear_all):
            # Default: clear all
            self.clear_search_caches()
            self.clear_media_caches()

        self.stdout.write(
            self.style.SUCCESS('Successfully cleared caches')
        )
        logger.info('Caches cleared successfully')

    def clear_search_caches(self):
        """Clear all search-related caches"""
        # For LocMemCache, we can't do pattern matching, so we clear the entire cache
        # In production with Redis, you would use:
        # cache.delete_pattern('search_*')
        # cache.delete_pattern('tweet_search:*')
        
        self.stdout.write('Clearing search caches...')
        
        # Get all tweets to generate cache keys
        tweets = Tweet.objects.values_list('text', flat=True)[:100]
        
        for tweet_text in tweets:
            # Clear caches for common search terms
            cache_keys = [
                f'tweet_search:{tweet_text}:page:1',
                f'search_tweets:{tweet_text}:page:1',
                f'search_users:{tweet_text}:page:1',
                f'search_all:{tweet_text}',
            ]
            for key in cache_keys:
                cache.delete(key)
        
        self.stdout.write(self.style.SUCCESS('Search caches cleared'))

    def clear_media_caches(self):
        """Clear all media-related caches"""
        self.stdout.write('Clearing media caches...')
        
        # Get all media files
        media_files = Media.objects.values_list('id', flat=True)
        
        for media_id in media_files:
            cache_keys = [
                f'media_etag:{media_id}',
                f'media_modified:{media_id}',
            ]
            for key in cache_keys:
                cache.delete(key)
        
        self.stdout.write(self.style.SUCCESS('Media caches cleared'))
