"""
Performance optimization utilities for media file serving and caching.
"""

from django.core.cache import cache
from django.http import FileResponse
from django.utils.http import http_date
from django.views.decorators.http import condition
from django.conf import settings
import os
import mimetypes
from datetime import datetime, timedelta


def get_media_etag(media_id):
    """Generate ETag for media file caching"""
    cache_key = f'media_etag:{media_id}'
    etag = cache.get(cache_key)
    
    if not etag:
        etag = f'"{media_id}-{datetime.now().timestamp()}"'
        cache.set(cache_key, etag, 86400)  # Cache for 24 hours
    
    return etag


def get_media_last_modified(media_id):
    """Get last modified time for media file"""
    from .models import Media
    
    cache_key = f'media_modified:{media_id}'
    last_modified = cache.get(cache_key)
    
    if not last_modified:
        try:
            media = Media.objects.get(id=media_id)
            last_modified = media.uploaded_at
            cache.set(cache_key, last_modified, 86400)  # Cache for 24 hours
        except Media.DoesNotExist:
            last_modified = None
    
    return last_modified


def optimize_media_response(file_path, media_id):
    """
    Optimize media file response with proper headers for caching and compression.
    
    Args:
        file_path: Path to the media file
        media_id: ID of the media object for caching
    
    Returns:
        FileResponse with optimized headers
    """
    if not os.path.exists(file_path):
        return None
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Create response
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    
    # Add caching headers
    etag = get_media_etag(media_id)
    last_modified = get_media_last_modified(media_id)
    
    response['ETag'] = etag
    if last_modified:
        response['Last-Modified'] = http_date(last_modified.timestamp())
    
    # Add cache control headers (cache for 30 days)
    response['Cache-Control'] = 'public, max-age=2592000'
    
    # Add content length
    response['Content-Length'] = file_size
    
    # Add content disposition for downloads
    filename = os.path.basename(file_path)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response


def clear_media_cache(media_id):
    """Clear cached data for a specific media file"""
    cache_keys = [
        f'media_etag:{media_id}',
        f'media_modified:{media_id}',
    ]
    
    for key in cache_keys:
        cache.delete(key)


def clear_search_cache(query=None):
    """
    Clear search result cache.
    
    Args:
        query: Specific query to clear, or None to clear all search caches
    """
    if query:
        cache_keys = [
            f'tweet_search:{query}:page:*',
            f'search_tweets:{query}:page:*',
            f'search_users:{query}:page:*',
            f'search_all:{query}',
        ]
        for key in cache_keys:
            # For wildcard patterns, we need to iterate through cache
            if '*' in key:
                # This is a limitation of LocMemCache - we can't do wildcard deletes
                # In production, use Redis which supports pattern matching
                pass
            else:
                cache.delete(key)
    else:
        # Clear all search caches (only works with Redis in production)
        # For LocMemCache, we'd need to track all keys
        pass


def get_query_optimization_stats():
    """
    Get statistics about query optimization and caching.
    
    Returns:
        Dictionary with cache and query stats
    """
    stats = {
        'cache_backend': settings.CACHES['default']['BACKEND'],
        'cache_timeout': settings.CACHES['default']['TIMEOUT'],
        'cache_max_entries': settings.CACHES['default']['OPTIONS'].get('MAX_ENTRIES', 'unlimited'),
    }
    
    return stats
