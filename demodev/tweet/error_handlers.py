"""
Error handling and validation utilities for the tweet application.
Provides centralized error handling, logging, and user-friendly error messages.
"""

import logging
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from functools import wraps

# Get logger for this module
logger = logging.getLogger('tweet')


class ValidationError(Exception):
    """Custom validation error for application-specific validation failures"""
    def __init__(self, message, error_code=None, user_message=None):
        self.message = message
        self.error_code = error_code or 'VALIDATION_ERROR'
        self.user_message = user_message or message
        super().__init__(self.message)


class FileUploadError(ValidationError):
    """Error for file upload validation failures"""
    def __init__(self, message, error_code='FILE_UPLOAD_ERROR', user_message=None):
        super().__init__(message, error_code, user_message)


class SearchError(ValidationError):
    """Error for search operation failures"""
    def __init__(self, message, error_code='SEARCH_ERROR', user_message=None):
        super().__init__(message, error_code, user_message)


class TweetEditError(ValidationError):
    """Error for tweet editing failures"""
    def __init__(self, message, error_code='TWEET_EDIT_ERROR', user_message=None):
        super().__init__(message, error_code, user_message)


class SchedulingError(ValidationError):
    """Error for tweet scheduling failures"""
    def __init__(self, message, error_code='SCHEDULING_ERROR', user_message=None):
        super().__init__(message, error_code, user_message)


def handle_file_upload_error(func):
    """
    Decorator to handle file upload errors in AJAX endpoints.
    Logs errors and returns appropriate JSON responses.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except FileUploadError as e:
            logger.warning(f"File upload error: {e.message}", extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
                'error_code': e.error_code
            })
            return JsonResponse({
                'success': False,
                'error': e.user_message,
                'error_code': e.error_code
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in file upload: {str(e)}", exc_info=True, extra={
                'user_id': request.user.id if request.user.is_authenticated else None
            })
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred while uploading the file. Please try again.',
                'error_code': 'UPLOAD_FAILED'
            }, status=500)
    return wrapper


def handle_search_error(func):
    """
    Decorator to handle search operation errors.
    Logs errors and returns appropriate responses.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except SearchError as e:
            logger.warning(f"Search error: {e.message}", extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
                'error_code': e.error_code
            })
            messages.error(request, e.user_message)
            return func(request, *args, **kwargs)  # Return default response
        except Exception as e:
            logger.error(f"Unexpected error in search: {str(e)}", exc_info=True, extra={
                'user_id': request.user.id if request.user.is_authenticated else None
            })
            messages.error(request, 'An error occurred while searching. Please try again.')
            return func(request, *args, **kwargs)  # Return default response
    return wrapper


def handle_tweet_edit_error(func):
    """
    Decorator to handle tweet editing errors.
    Logs errors and returns appropriate responses.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except TweetEditError as e:
            logger.warning(f"Tweet edit error: {e.message}", extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
                'error_code': e.error_code
            })
            messages.error(request, e.user_message)
            return func(request, *args, **kwargs)  # Return default response
        except Exception as e:
            logger.error(f"Unexpected error in tweet edit: {str(e)}", exc_info=True, extra={
                'user_id': request.user.id if request.user.is_authenticated else None
            })
            messages.error(request, 'An error occurred while editing the tweet. Please try again.')
            return func(request, *args, **kwargs)  # Return default response
    return wrapper


def handle_scheduling_error(func):
    """
    Decorator to handle tweet scheduling errors.
    Logs errors and returns appropriate responses.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except SchedulingError as e:
            logger.warning(f"Scheduling error: {e.message}", extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
                'error_code': e.error_code
            })
            messages.error(request, e.user_message)
            return func(request, *args, **kwargs)  # Return default response
        except Exception as e:
            logger.error(f"Unexpected error in scheduling: {str(e)}", exc_info=True, extra={
                'user_id': request.user.id if request.user.is_authenticated else None
            })
            messages.error(request, 'An error occurred while scheduling the tweet. Please try again.')
            return func(request, *args, **kwargs)  # Return default response
    return wrapper


def validate_file_upload(file, max_size_mb=5, allowed_types=None):
    """
    Validate uploaded file for size and type.
    
    Args:
        file: The uploaded file object
        max_size_mb: Maximum file size in megabytes
        allowed_types: List of allowed MIME types
        
    Raises:
        FileUploadError: If validation fails
    """
    if allowed_types is None:
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
    
    if not file:
        raise FileUploadError(
            'No file provided',
            'NO_FILE',
            'Please select a file to upload.'
        )
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        size_mb = file.size / (1024 * 1024)
        raise FileUploadError(
            f'File size {size_mb:.2f}MB exceeds maximum {max_size_mb}MB',
            'FILE_TOO_LARGE',
            f'File size must be less than {max_size_mb}MB. Your file is {size_mb:.2f}MB.'
        )
    
    # Check file type
    if file.content_type not in allowed_types:
        raise FileUploadError(
            f'Invalid file type: {file.content_type}',
            'INVALID_FILE_TYPE',
            f'Only JPEG, PNG, and GIF images are allowed. Your file type is {file.content_type}.'
        )
    
    logger.info(f"File validation passed: {file.name} ({file.size} bytes)")


def validate_tweet_edit(tweet, user):
    """
    Validate that a user can edit a tweet.
    
    Args:
        tweet: The tweet object to edit
        user: The user attempting to edit
        
    Raises:
        TweetEditError: If validation fails
    """
    if not tweet:
        raise TweetEditError(
            'Tweet not found',
            'TWEET_NOT_FOUND',
            'The tweet you are trying to edit does not exist.'
        )
    
    if tweet.user != user:
        logger.warning(f"Unauthorized edit attempt: user {user.id} tried to edit tweet {tweet.id} by user {tweet.user.id}")
        raise TweetEditError(
            f'User {user.id} attempted to edit tweet {tweet.id} owned by {tweet.user.id}',
            'UNAUTHORIZED_EDIT',
            'You do not have permission to edit this tweet.'
        )
    
    logger.info(f"Tweet edit validation passed: user {user.id} can edit tweet {tweet.id}")


def validate_scheduled_time(scheduled_time):
    """
    Validate that a scheduled publish time is in the future.
    
    Args:
        scheduled_time: The datetime object for scheduled publishing
        
    Raises:
        SchedulingError: If validation fails
    """
    if not scheduled_time:
        return  # Optional field
    
    now = timezone.now()
    if scheduled_time <= now:
        raise SchedulingError(
            f'Scheduled time {scheduled_time} is not in the future (now: {now})',
            'PAST_SCHEDULED_TIME',
            'Scheduled time must be in the future.'
        )
    
    logger.info(f"Scheduled time validation passed: {scheduled_time}")


def validate_search_query(query):
    """
    Validate search query.
    
    Args:
        query: The search query string
        
    Raises:
        SearchError: If validation fails
    """
    if not query:
        return  # Empty query is allowed
    
    if len(query) > 500:
        raise SearchError(
            f'Search query too long: {len(query)} characters',
            'QUERY_TOO_LONG',
            'Search query must be 500 characters or less.'
        )
    
    logger.info(f"Search query validation passed: '{query}'")


def log_file_upload(user, file_name, file_size, file_type):
    """Log file upload activity"""
    logger.info(f"File uploaded: {file_name} ({file_size} bytes, {file_type})", extra={
        'user_id': user.id,
        'file_name': file_name,
        'file_size': file_size,
        'file_type': file_type
    })


def log_tweet_edit(user, tweet_id, previous_content, new_content):
    """Log tweet edit activity"""
    logger.info(f"Tweet edited: {tweet_id}", extra={
        'user_id': user.id,
        'tweet_id': tweet_id,
        'previous_length': len(previous_content),
        'new_length': len(new_content)
    })


def log_tweet_scheduled(user, tweet_id, scheduled_time):
    """Log tweet scheduling activity"""
    logger.info(f"Tweet scheduled: {tweet_id} for {scheduled_time}", extra={
        'user_id': user.id,
        'tweet_id': tweet_id,
        'scheduled_time': scheduled_time.isoformat()
    })


def log_search_query(user, query, result_count):
    """Log search activity"""
    logger.info(f"Search performed: '{query}' returned {result_count} results", extra={
        'user_id': user.id if user.is_authenticated else None,
        'query': query,
        'result_count': result_count
    })
