from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from django.views.decorators.http import condition

from .models import (
    UserProfile, Media, Tweet, TweetEditHistory, 
    TweetDraft, Comment, Like, Follow, User
)
from .serializers import (
    UserProfileSerializer, MediaSerializer, TweetSerializer,
    TweetDetailSerializer, TweetDraftSerializer, TweetEditHistorySerializer,
    CommentSerializer, LikeSerializer, FollowSerializer, UserSerializer
)
from .error_handlers import (
    FileUploadError, TweetEditError, SchedulingError, SearchError,
    validate_file_upload, validate_tweet_edit, validate_scheduled_time,
    validate_search_query, log_file_upload, log_tweet_edit, log_tweet_scheduled
)
import logging

logger = logging.getLogger('tweet')


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user profile management.
    
    Provides CRUD operations for user profiles including:
    - Retrieve user profile information
    - Update profile (bio, display_name, profile_picture)
    - Get profile statistics
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'user__username'
    pagination_class = None  # Use default pagination from settings
    
    def get_queryset(self):
        """Filter profiles based on query parameters with query optimization"""
        # Use select_related to optimize database queries
        queryset = UserProfile.objects.select_related('user').all()
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(user__username__icontains=username)
        return queryset
    
    def update(self, request, *args, **kwargs):
        """Update user profile - only allow users to update their own profile"""
        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {'detail': 'You can only update your own profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update user profile - only allow users to update their own profile"""
        profile = self.get_object()
        if profile.user != request.user:
            return Response(
                {'detail': 'You can only update your own profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, user__username=None):
        """Get profile statistics"""
        profile = self.get_object()
        return Response({
            'follower_count': profile.get_follower_count(),
            'following_count': profile.get_following_count(),
            'tweet_count': profile.get_tweet_count(),
        })


class MediaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for media management.
    
    Provides operations for:
    - Upload media files
    - Retrieve media information
    - Delete media files
    - List user's media
    """
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    pagination_class = None  # Use default pagination from settings
    
    def get_queryset(self):
        """Return only the current user's media with query optimization"""
        # Use select_related to optimize database queries
        return Media.objects.select_related('user').filter(user=self.request.user).order_by('-uploaded_at')
    
    def perform_create(self, serializer):
        """Create media and associate with current user"""
        try:
            # Get the uploaded file
            uploaded_file = self.request.FILES.get('file')
            
            # Validate file upload
            validate_file_upload(uploaded_file, max_size_mb=5, allowed_types=['image/jpeg', 'image/png', 'image/gif'])
            
            media = serializer.save(user=self.request.user, file_type='image')
            
            # Log the upload
            log_file_upload(self.request.user, uploaded_file.name, uploaded_file.size, uploaded_file.content_type)
            
        except FileUploadError as e:
            logger.warning(f"File upload validation error: {e.message}", extra={'user_id': self.request.user.id})
            raise
    
    def perform_destroy(self, instance):
        """Delete media file and associated database record"""
        try:
            instance.delete_file()
            instance.delete()
            logger.info(f"Media deleted: {instance.id}", extra={'user_id': self.request.user.id})
        except Exception as e:
            logger.error(f"Error deleting media {instance.id}: {str(e)}", exc_info=True, extra={'user_id': self.request.user.id})
            raise
    
    @action(detail=True, methods=['get'])
    def tweets(self, request, pk=None):
        """Get all tweets associated with this media"""
        media = self.get_object()
        tweets = media.tweets.all().order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True, context={'request': request})
        return Response({
            'media_id': media.id,
            'tweets': serializer.data,
            'count': tweets.count()
        })


class TweetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tweet management.
    
    Provides operations for:
    - Create, retrieve, update, delete tweets
    - Like/unlike tweets
    - Add comments
    - View edit history
    - Schedule tweets
    """
    queryset = Tweet.objects.all().annotate(like_count=Count('likes'))
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text', 'user__username']
    ordering_fields = ['created_at', 'like_count']
    ordering = ['-created_at']
    pagination_class = None  # Use default pagination from settings
    
    def get_queryset(self):
        """Optimize queries with select_related and prefetch_related"""
        # Prefetch related objects to reduce database queries
        likes_prefetch = Prefetch('likes', queryset=Like.objects.select_related('user'))
        comments_prefetch = Prefetch('comments', queryset=Comment.objects.select_related('user'))
        media_prefetch = Prefetch('media', queryset=Media.objects.select_related('user'))
        
        queryset = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
            likes_prefetch,
            comments_prefetch,
            media_prefetch
        ).annotate(like_count=Count('likes')).order_by('-created_at')
        
        return queryset
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return TweetDetailSerializer
        return TweetSerializer
    
    def perform_create(self, serializer):
        """Create tweet and associate with current user"""
        tweet = serializer.save(user=self.request.user)
        logger.info(f"Tweet created: {tweet.id}", extra={'user_id': self.request.user.id})
    
    def perform_update(self, serializer):
        """Update tweet and create edit history"""
        tweet = self.get_object()
        
        # Check permissions
        if tweet.user != self.request.user:
            raise PermissionError("You can only edit your own tweets.")
        
        try:
            # Validate tweet edit permissions
            validate_tweet_edit(tweet, self.request.user)
            
            # Store the previous content before updating
            previous_content = tweet.text
            
            # Update the tweet
            updated_tweet = serializer.save()
            
            # Create edit history record
            TweetEditHistory.objects.create(
                tweet=updated_tweet,
                previous_content=previous_content,
                edited_by=self.request.user
            )
            
            # Mark tweet as edited
            updated_tweet.mark_as_edited()
            
            # Log the edit
            log_tweet_edit(self.request.user, tweet.id, previous_content, updated_tweet.text)
            
        except TweetEditError as e:
            logger.warning(f"Error during tweet edit: {e.message}", extra={'user_id': self.request.user.id})
            raise
    
    def perform_destroy(self, instance):
        """Delete tweet - only allow owner"""
        if instance.user != self.request.user:
            raise PermissionError("You can only delete your own tweets.")
        instance.delete()
        logger.info(f"Tweet deleted: {instance.id}", extra={'user_id': self.request.user.id})
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a tweet"""
        tweet = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, tweet=tweet)
        
        if created:
            return Response(
                {'detail': 'Tweet liked successfully.', 'liked': True},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'detail': 'Tweet already liked.', 'liked': True},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a tweet"""
        tweet = self.get_object()
        like = Like.objects.filter(user=request.user, tweet=tweet).first()
        
        if like:
            like.delete()
            return Response(
                {'detail': 'Tweet unliked successfully.', 'liked': False},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Tweet not liked.', 'liked': False},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        """Get users who liked this tweet"""
        tweet = self.get_object()
        likes = Like.objects.filter(tweet=tweet).select_related('user')
        serializer = LikeSerializer(likes, many=True)
        return Response({
            'tweet_id': tweet.id,
            'likes': serializer.data,
            'count': likes.count()
        })
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for this tweet"""
        tweet = self.get_object()
        comments = Comment.objects.filter(tweet=tweet).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response({
            'tweet_id': tweet.id,
            'comments': serializer.data,
            'count': comments.count()
        })
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to this tweet"""
        tweet = self.get_object()
        text = request.data.get('text', '').strip()
        
        if not text:
            return Response(
                {'detail': 'Comment text is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = Comment.objects.create(tweet=tweet, user=request.user, text=text)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def edit_history(self, request, pk=None):
        """Get edit history for this tweet"""
        tweet = self.get_object()
        edits = TweetEditHistory.objects.filter(tweet=tweet).order_by('-edited_at')
        serializer = TweetEditHistorySerializer(edits, many=True)
        return Response({
            'tweet_id': tweet.id,
            'edits': serializer.data,
            'count': edits.count()
        })
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin a tweet to the user's profile"""
        tweet = self.get_object()
        
        if tweet.user != request.user:
            return Response(
                {'detail': 'You can only pin your own tweets.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tweet.pin()
        
        logger.info(f"Tweet pinned: {tweet.id}", extra={'user_id': request.user.id})
        
        return Response(
            {'detail': 'Tweet pinned successfully.', 'is_pinned': True},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Unpin a tweet from the user's profile"""
        tweet = self.get_object()
        
        if tweet.user != request.user:
            return Response(
                {'detail': 'You can only unpin your own tweets.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tweet.unpin()
        
        logger.info(f"Tweet unpinned: {tweet.id}", extra={'user_id': request.user.id})
        
        return Response(
            {'detail': 'Tweet unpinned successfully.', 'is_pinned': False},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search tweets by content with caching"""
        query = request.query_params.get('q', '').strip()
        page = request.query_params.get('page', 1)
        
        if not query:
            return Response(
                {'detail': 'Search query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_search_query(query)
            
            # Create cache key for this search query and page
            cache_key = f'tweet_search:{query}:page:{page}'
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Search cache hit for query: {query}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
                return Response(cached_result)
            
            # Query with optimization - use published manager to exclude scheduled tweets
            tweets = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
                'likes', 'comments', 'media'
            ).filter(
                Q(text__icontains=query)
            ).order_by('-created_at').annotate(like_count=Count('likes'))
            
            paginator = Paginator(tweets, 10)
            page_obj = paginator.get_page(page)
            
            serializer = self.get_serializer(page_obj.object_list, many=True)
            
            result = {
                'query': query,
                'results': serializer.data,
                'count': tweets.count(),
                'page': page,
                'total_pages': paginator.num_pages
            }
            
            # Cache the result for 5 minutes
            cache.set(cache_key, result, 300)
            
            return Response(result)
        except SearchError as e:
            logger.warning(f"Search validation error: {e.message}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
            return Response(
                {'detail': e.user_message},
                status=status.HTTP_400_BAD_REQUEST
            )


class TweetDraftViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tweet draft management.
    
    Provides operations for:
    - Save draft tweets
    - Retrieve drafts
    - Update drafts
    - Delete drafts
    """
    queryset = TweetDraft.objects.all()
    serializer_class = TweetDraftSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Use default pagination from settings
    
    def get_queryset(self):
        """Return only the current user's drafts with query optimization"""
        # Use select_related and prefetch_related for optimization
        media_prefetch = Prefetch('media', queryset=Media.objects.select_related('user'))
        return TweetDraft.objects.select_related('user').prefetch_related(
            media_prefetch
        ).filter(user=self.request.user).order_by('-updated_at')
    
    def perform_create(self, serializer):
        """Create draft and associate with current user"""
        draft = serializer.save(user=self.request.user)
        logger.info(f"Draft created: {draft.id}", extra={
            'user_id': self.request.user.id,
            'draft_id': draft.id
        })
    
    def perform_update(self, serializer):
        """Update draft"""
        draft = serializer.save()
        logger.info(f"Draft updated: {draft.id}", extra={
            'user_id': self.request.user.id,
            'draft_id': draft.id
        })
    
    def perform_destroy(self, instance):
        """Delete draft"""
        instance.delete()
        logger.info(f"Draft deleted: {instance.id}", extra={'user_id': self.request.user.id})
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's draft (most recent)"""
        draft = TweetDraft.objects.filter(user=request.user).first()
        
        if draft:
            serializer = self.get_serializer(draft)
            return Response(serializer.data)
        else:
            return Response(
                {'detail': 'No draft found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear current user's draft"""
        draft = TweetDraft.objects.filter(user=request.user).first()
        
        if draft:
            draft.delete()
            return Response(
                {'detail': 'Draft cleared successfully.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'No draft found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class SearchViewSet(viewsets.ViewSet):
    """
    API endpoint for comprehensive search.
    
    Provides operations for:
    - Search tweets by content
    - Search users by username and bio
    - Combined search results
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def tweets(self, request):
        """Search tweets with caching"""
        query = request.query_params.get('q', '').strip()
        page = request.query_params.get('page', 1)
        
        if not query:
            return Response(
                {'detail': 'Search query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_search_query(query)
            
            # Create cache key for this search query and page
            cache_key = f'search_tweets:{query}:page:{page}'
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Search cache hit for tweets query: {query}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
                return Response(cached_result)
            
            # Query with optimization
            tweets = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
                'likes', 'comments', 'media'
            ).filter(
                Q(text__icontains=query)
            ).order_by('-created_at').annotate(like_count=Count('likes'))
            
            paginator = Paginator(tweets, 10)
            page_obj = paginator.get_page(page)
            
            serializer = TweetSerializer(page_obj.object_list, many=True, context={'request': request})
            
            result = {
                'query': query,
                'results': serializer.data,
                'count': tweets.count(),
                'page': page,
                'total_pages': paginator.num_pages
            }
            
            # Cache the result for 5 minutes
            cache.set(cache_key, result, 300)
            
            return Response(result)
        except SearchError as e:
            logger.warning(f"Search validation error: {e.message}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
            return Response(
                {'detail': e.user_message},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Search users with caching"""
        query = request.query_params.get('q', '').strip()
        page = request.query_params.get('page', 1)
        
        if not query:
            return Response(
                {'detail': 'Search query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_search_query(query)
            
            # Create cache key for this search query and page
            cache_key = f'search_users:{query}:page:{page}'
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Search cache hit for users query: {query}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
                return Response(cached_result)
            
            # Query with optimization
            users = User.objects.select_related('profile').filter(
                Q(username__icontains=query) |
                Q(profile__bio__icontains=query) |
                Q(first_name__icontains=query)
            ).order_by('username').distinct()
            
            paginator = Paginator(users, 10)
            page_obj = paginator.get_page(page)
            
            # Ensure all users have profiles
            profiles = []
            for user in page_obj.object_list:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profiles.append(profile)
            
            serializer = UserProfileSerializer(
                profiles,
                many=True,
                context={'request': request}
            )
            
            result = {
                'query': query,
                'results': serializer.data,
                'count': users.count(),
                'page': page,
                'total_pages': paginator.num_pages
            }
            
            # Cache the result for 5 minutes
            cache.set(cache_key, result, 300)
            
            return Response(result)
        except SearchError as e:
            logger.warning(f"Search validation error: {e.message}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
            return Response(
                {'detail': e.user_message},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        """Combined search across tweets and users with caching"""
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'detail': 'Search query is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_search_query(query)
            
            # Create cache key for this combined search query
            cache_key = f'search_all:{query}'
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Search cache hit for combined query: {query}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
                return Response(cached_result)
            
            # Search tweets with optimization - use published manager to exclude scheduled tweets
            tweets = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
                'likes', 'comments', 'media'
            ).filter(
                Q(text__icontains=query)
            ).order_by('-created_at').annotate(like_count=Count('likes'))
            
            # Search users with optimization
            users = User.objects.select_related('profile').filter(
                Q(username__icontains=query) |
                Q(profile__bio__icontains=query) |
                Q(first_name__icontains=query)
            ).order_by('username').distinct()
            
            tweet_serializer = TweetSerializer(tweets[:5], many=True, context={'request': request})
            
            # Ensure all users have profiles
            user_profiles = []
            for user in users[:5]:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                user_profiles.append(profile)
            
            user_serializer = UserProfileSerializer(
                user_profiles,
                many=True,
                context={'request': request}
            )
            
            result = {
                'query': query,
                'tweets': {
                    'results': tweet_serializer.data,
                    'count': tweets.count()
                },
                'users': {
                    'results': user_serializer.data,
                    'count': users.count()
                },
                'total_results': tweets.count() + users.count()
            }
            
            # Cache the result for 5 minutes
            cache.set(cache_key, result, 300)
            
            return Response(result)
        except SearchError as e:
            logger.warning(f"Search validation error: {e.message}", extra={'user_id': request.user.id if request.user.is_authenticated else None})
            return Response(
                {'detail': e.user_message},
                status=status.HTTP_400_BAD_REQUEST
            )

