from django.shortcuts import redirect, render, get_object_or_404
from .models import Tweet, Follow, Comment, Like, UserProfile, Media, TweetEditHistory, TweetDraft
from .forms import TweetForm, UserRegistrationForm, UserProfileForm, MediaUploadForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .tokens import email_verification_token
from .error_handlers import (
    handle_file_upload_error, handle_search_error, handle_tweet_edit_error,
    handle_scheduling_error, validate_file_upload, validate_tweet_edit,
    validate_scheduled_time, validate_search_query, log_file_upload,
    log_tweet_edit, log_tweet_scheduled, log_search_query, FileUploadError,
    TweetEditError, SchedulingError, SearchError
)
import json
import logging

logger = logging.getLogger('tweet')

def index(request):
    # Query optimization with select_related and prefetch_related
    tweets_queryset = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
        'likes', 'comments', 'media'
    ).order_by('-created_at').annotate(
        like_count=Count('likes')
    )
    
    # Paginate tweets (10 per page)
    page_num = request.GET.get('page', 1)
    paginator = Paginator(tweets_queryset, 10)
    tweets_page = paginator.get_page(page_num)
    tweets = tweets_page.object_list
    
    # Add user_has_liked flag for authenticated users
    if request.user.is_authenticated:
        for tweet in tweets:
            tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
    
    return render(request, "index.html", {'tweets': tweets, 'tweets_page': tweets_page})

def tweet_List(request):
    # Query optimization with select_related and prefetch_related
    tweets_queryset = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
        'likes', 'comments', 'media'
    ).order_by('-created_at').annotate(
        like_count=Count('likes')
    )
    
    # Paginate tweets (10 per page)
    page_num = request.GET.get('page', 1)
    paginator = Paginator(tweets_queryset, 10)
    tweets_page = paginator.get_page(page_num)
    tweets = tweets_page.object_list
    
    # Add user_has_liked flag for authenticated users
    if request.user.is_authenticated:
        for tweet in tweets:
            tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
    
    return render(request, 'tweet_list.html', {'tweets': tweets, 'tweets_page': tweets_page})

@login_required(login_url='login')
def tweet_Create(request):
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                tweet = form.save(commit=False)
                tweet.user = request.user
                tweet.save()
                
                # Handle media association from form
                form.save()  # This will handle media.set() via the form's save method
                
                logger.info(f"Tweet created: {tweet.id}", extra={'user_id': request.user.id})
                messages.success(request, 'Tweet created successfully!')
                
                return redirect('tweet_list')
            except Exception as e:
                logger.error(f"Error creating tweet: {str(e)}", exc_info=True, extra={'user_id': request.user.id})
                messages.error(request, 'An error occurred while creating the tweet. Please try again.')
        else:
            # Log form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form validation error - {field}: {error}", extra={'user_id': request.user.id})
                    messages.error(request, f"{field}: {error}")
    else:
        form = TweetForm()
    return render(request, 'tweet_form.html', {'form': form})

@login_required(login_url='login')
def Tweet_Edit(request, tweet_id):
    try:
        tweet = Tweet.objects.get(pk=tweet_id, user=request.user)
    except Tweet.DoesNotExist:
        logger.warning(f"Edit attempt on non-existent or unauthorized tweet: {tweet_id}", extra={'user_id': request.user.id})
        messages.error(request, 'Tweet not found or you do not have permission to edit it.')
        return redirect('tweet_list')
    
    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            try:
                # Validate tweet edit permissions
                validate_tweet_edit(tweet, request.user)
                
                # Store the previous content before updating
                previous_content = tweet.text
                
                # Update the tweet
                tweet = form.save(commit=False)
                tweet.user = request.user
                tweet.save()
                
                # Handle media association via form's save method
                form.save()
                
                # Create edit history record
                TweetEditHistory.objects.create(
                    tweet=tweet,
                    previous_content=previous_content,
                    edited_by=request.user
                )
                
                # Mark tweet as edited
                tweet.mark_as_edited()
                
                # Log the edit
                log_tweet_edit(request.user, tweet.id, previous_content, tweet.text)
                
                messages.success(request, 'Tweet updated successfully!')
                return redirect('tweet_detail', tweet_id=tweet.id)
            except TweetEditError as e:
                logger.warning(f"Tweet edit error: {e.message}", extra={'user_id': request.user.id})
                messages.error(request, e.user_message)
            except Exception as e:
                logger.error(f"Error editing tweet {tweet_id}: {str(e)}", exc_info=True, extra={'user_id': request.user.id})
                messages.error(request, 'An error occurred while editing the tweet. Please try again.')
        else:
            # Log form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form validation error during edit - {field}: {error}", extra={'user_id': request.user.id})
                    messages.error(request, f"{field}: {error}")
    else:
        form = TweetForm(instance=tweet)
    return render(request, 'tweet_form.html', {'form': form})

@login_required(login_url='login')
def Tweet_Delete(request, tweet_id):
    try:
        tweet = Tweet.objects.get(pk=tweet_id, user=request.user)
    except Tweet.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Tweet not found'}, status=404)
        messages.error(request, 'Tweet not found or you do not have permission to delete it.')
        return redirect('tweet_list')
    
    if request.method == "POST":
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            tweet.delete()
            return JsonResponse({'success': True})
        
        # Regular request
        tweet.delete()
        messages.success(request, 'Tweet deleted successfully!')
        return redirect('tweet_list')
    return render(request, 'tweet_confirm_delete.html', {'tweet': tweet})

def register(request):
    """Register a new user and send email verification link"""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user but keep inactive until email verification
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                
                # Generate verification token and link
                current_site = get_current_site(request)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = email_verification_token.make_token(user)
                
                # Prepare email
                mail_subject = 'Verify your email - Tweet App'
                message = render_to_string('email_verification.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                    'protocol': 'https' if request.is_secure() else 'http',
                })
                
                email = EmailMessage(
                    mail_subject,
                    message,
                    from_email='noreply@tweetapp.com',
                    to=[user.email]
                )
                email.send()
                
                logger.info(f"Verification email sent to {user.email}", extra={'user_id': user.id})
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
                
                return render(request, 'check_email.html', {'email': user.email})
            
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}", exc_info=True)
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def activate_email(request, uidb64, token):
    """Activate user account via email verification link"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        logger.info(f"Email verified for user {user.username}", extra={'user_id': user.id})
        messages.success(request, 'Email verified successfully! You can now login.')
        
        return redirect('login')
    else:
        logger.warning(f"Invalid or expired verification link attempted")
        messages.error(request, 'Activation link is invalid or has expired.')
        
        return redirect('register')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('index')

# Follow/Unfollow functionality
@login_required(login_url='login')
def user_list(request):
    # Query optimization with select_related
    users_queryset = User.objects.select_related('profile').exclude(id=request.user.id).order_by('username')
    
    # Paginate users (10 per page)
    page_num = request.GET.get('page', 1)
    paginator = Paginator(users_queryset, 10)
    users_page = paginator.get_page(page_num)
    users = users_page.object_list
    
    # Get follow status for each user
    for user in users:
        follow_request = Follow.objects.filter(follower=request.user, following=user).first()
        if follow_request:
            user.follow_status = 'accepted' if follow_request.is_accepted else 'pending'
        else:
            user.follow_status = 'none'
    
    return render(request, 'user_list.html', {'users': users, 'users_page': users_page})

@login_required(login_url='login')
def send_follow_request(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if user_to_follow == request.user:
        messages.error(request, 'You cannot follow yourself!')
        return redirect('user_list')
    
    follow_request, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if created:
        messages.success(request, f'Follow request sent to {user_to_follow.username}!')
    else:
        messages.info(request, f'Follow request already sent to {user_to_follow.username}.')
    
    return redirect('user_list')

@login_required(login_url='login')
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    messages.success(request, f'You unfollowed {user_to_unfollow.username}!')
    
    return redirect('user_list')

@login_required(login_url='login')
def follow_requests(request):
    # Query optimization with select_related
    pending_requests_queryset = Follow.objects.select_related('follower', 'follower__profile').filter(
        following=request.user, is_accepted=False
    ).order_by('-created_at')
    
    # Paginate follow requests (10 per page)
    page_num = request.GET.get('page', 1)
    paginator = Paginator(pending_requests_queryset, 10)
    requests_page = paginator.get_page(page_num)
    pending_requests = requests_page.object_list
    
    return render(request, 'follow_requests.html', {
        'pending_requests': pending_requests,
        'requests_page': requests_page
    })

@login_required(login_url='login')
def accept_follow_request(request, request_id):
    follow_request = get_object_or_404(Follow, id=request_id, following=request.user)
    follow_request.is_accepted = True
    follow_request.save()
    messages.success(request, f'You accepted {follow_request.follower.username}\'s follow request!')
    return redirect('follow_requests')

@login_required(login_url='login')
def reject_follow_request(request, request_id):
    follow_request = get_object_or_404(Follow, id=request_id, following=request.user)
    follow_request.delete()
    messages.success(request, f'You rejected {follow_request.follower.username}\'s follow request!')
    return redirect('follow_requests')

# Comment functionality
@login_required(login_url='login')
def tweet_detail(request, tweet_id):
    # Query optimization with select_related and prefetch_related
    tweet = get_object_or_404(
        Tweet.objects.select_related('user', 'user__profile').prefetch_related(
            'likes', 'media'
        ),
        id=tweet_id
    )
    
    # Get comments with query optimization
    comments = tweet.comments.select_related('user', 'user__profile').all().order_by('-created_at')
    
    # Check if user has liked this tweet
    user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
    like_count = tweet.likes.count()
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        if comment_text:
            Comment.objects.create(
                tweet=tweet,
                user=request.user,
                text=comment_text
            )
            messages.success(request, 'Comment added successfully!')
            return redirect('tweet_detail', tweet_id=tweet.id)
    
    return render(request, 'tweet_detail.html', {
        'tweet': tweet,
        'comments': comments,
        'user_has_liked': user_has_liked,
        'like_count': like_count
    })

@login_required(login_url='login')
def add_comment_ajax(request, tweet_id):
    """AJAX endpoint to add a comment"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment_text', '').strip()
            
            if not comment_text:
                return JsonResponse({'success': False, 'error': 'Comment text is required'}, status=400)
            
            tweet = get_object_or_404(Tweet, id=tweet_id)
            comment = Comment.objects.create(
                tweet=tweet,
                user=request.user,
                text=comment_text
            )
            
            # Calculate time ago
            from django.utils.timesince import timesince
            time_ago = timesince(comment.created_at) + ' ago'
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'time_ago': time_ago,
                    'can_delete': True,
                    'tweet_id': tweet_id
                },
                'comment_count': tweet.comments.count()
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    tweet_id = comment.tweet.id
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        comment.delete()
        comment_count = Comment.objects.filter(tweet_id=tweet_id).count()
        return JsonResponse({
            'success': True,
            'comment_count': comment_count
        })
    
    # Regular request
    comment.delete()
    messages.success(request, 'Comment deleted successfully!')
    return redirect('tweet_detail', tweet_id=tweet_id)

# Like functionality
@login_required(login_url='login')
def toggle_like(request, tweet_id):
    """AJAX endpoint to like/unlike a tweet"""
    if request.method == 'POST':
        tweet = get_object_or_404(Tweet, id=tweet_id)
        like, created = Like.objects.get_or_create(user=request.user, tweet=tweet)
        
        if not created:
            # Unlike - delete the like
            like.delete()
            liked = False
        else:
            liked = True
        
        # Get updated like count
        like_count = tweet.likes.count()
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': like_count
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
def tweet_likes(request, tweet_id):
    """Show users who liked a tweet"""
    tweet = get_object_or_404(Tweet, id=tweet_id)
    
    # Query optimization with select_related
    likes_queryset = Like.objects.select_related('user', 'user__profile').filter(
        tweet=tweet
    ).order_by('-created_at')
    
    # Paginate likes (10 per page)
    page_num = request.GET.get('page', 1)
    paginator = Paginator(likes_queryset, 10)
    likes_page = paginator.get_page(page_num)
    likes = likes_page.object_list
    
    return render(request, 'tweet_likes.html', {
        'tweet': tweet,
        'likes': likes,
        'likes_page': likes_page
    })


# Pin tweet functionality
@login_required(login_url='login')
def pin_tweet(request, tweet_id):
    """Pin a tweet to the user's profile"""
    if request.method == 'POST':
        tweet = get_object_or_404(Tweet, id=tweet_id)
        
        # Only the tweet author can pin their own tweets
        if tweet.user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You can only pin your own tweets'
            }, status=403)
        
        tweet.pin()
        
        return JsonResponse({
            'success': True,
            'pinned': True,
            'message': 'Tweet pinned to your profile'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def unpin_tweet(request, tweet_id):
    """Unpin a tweet from the user's profile"""
    if request.method == 'POST':
        tweet = get_object_or_404(Tweet, id=tweet_id)
        
        # Only the tweet author can unpin their own tweets
        if tweet.user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You can only unpin your own tweets'
            }, status=403)
        
        tweet.unpin()
        
        return JsonResponse({
            'success': True,
            'pinned': False,
            'message': 'Tweet unpinned from your profile'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def refresh_content(request):
    """AJAX endpoint for auto-refresh functionality"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        path = request.GET.get('path', '/')
        
        if path == '/' or path == '/tweets/':
            # Return fresh tweet data
            tweets = Tweet.objects.all().order_by('-created_at').annotate(
                like_count=Count('likes')
            )
            
            # Add user_has_liked flag for authenticated users
            if request.user.is_authenticated:
                for tweet in tweets:
                    tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
            
            return JsonResponse({
                'success': True,
                'tweet_count': tweets.count(),
                'latest_tweet_id': tweets.first().id if tweets.exists() else None,
                'timestamp': timezone.now().isoformat()
            })
        
        elif '/tweet/' in path:
            # Return fresh comment data for tweet detail
            tweet_id = path.split('/tweet/')[1].split('/')[0]
            try:
                tweet = Tweet.objects.get(id=tweet_id)
                return JsonResponse({
                    'success': True,
                    'comment_count': tweet.comments.count(),
                    'like_count': tweet.likes.count(),
                    'timestamp': timezone.now().isoformat()
                })
            except Tweet.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Tweet not found'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# Profile management views
def user_profile(request, username):
    """Display user profile with information and statistics"""
    user = get_object_or_404(User, username=username)
    # Ensure user has a profile, create one if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user's tweets with query optimization
    tweets_queryset = user.tweet_set.select_related('user', 'user__profile').prefetch_related(
        'likes', 'comments', 'media'
    ).order_by('-created_at').annotate(
        like_count=Count('likes')
    )
    
    # Paginate tweets (10 per page)
    page_num = request.GET.get('page', 1)
    paginator = Paginator(tweets_queryset, 10)
    tweets_page = paginator.get_page(page_num)
    tweets = tweets_page.object_list
    

    
    # Add user_has_liked flag for authenticated users
    if request.user.is_authenticated:
        for tweet in tweets:
            tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
    
    # Get follow status if viewing another user's profile
    follow_status = None
    if request.user.is_authenticated and request.user != user:
        follow_request = Follow.objects.filter(follower=request.user, following=user).first()
        if follow_request:
            follow_status = 'accepted' if follow_request.is_accepted else 'pending'
        else:
            follow_status = 'none'
    
    context = {
        'profile_user': user,
        'profile': profile,
        'tweets': tweets,
        'tweets_page': tweets_page,
        'follow_status': follow_status,
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    """Edit user profile information"""
    # Ensure user has a profile, create one if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile', username=request.user.username)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'edit_profile.html', {'form': form, 'profile': profile})




# Media management views
@login_required(login_url='login')
@handle_file_upload_error
def upload_media(request):
    """AJAX endpoint to upload media files"""
    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get the uploaded file
                uploaded_file = request.FILES.get('file')
                
                # Validate file upload
                validate_file_upload(uploaded_file, max_size_mb=5, allowed_types=['image/jpeg', 'image/png', 'image/gif'])
                
                media = form.save(commit=False)
                media.user = request.user
                media.file_type = 'image'  # Default to image for now
                media.save()
                
                # Log the upload
                log_file_upload(request.user, uploaded_file.name, uploaded_file.size, uploaded_file.content_type)
                
                return JsonResponse({
                    'success': True,
                    'media': {
                        'id': media.id,
                        'url': media.file.url,
                        'thumbnail_url': media.thumbnail.url if media.thumbnail else media.file.url,
                        'file_size': media.file_size,
                        'width': media.width,
                        'height': media.height,
                    }
                })
            except FileUploadError as e:
                logger.warning(f"File upload validation error: {e.message}", extra={'user_id': request.user.id})
                return JsonResponse({
                    'success': False,
                    'error': e.user_message,
                    'error_code': e.error_code
                }, status=400)
            except Exception as e:
                logger.error(f"Error saving media: {str(e)}", exc_info=True, extra={'user_id': request.user.id})
                return JsonResponse({
                    'success': False,
                    'error': 'An error occurred while saving the media file. Please try again.',
                    'error_code': 'SAVE_FAILED'
                }, status=500)
        else:
            # Return validation errors
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
                logger.warning(f"Form validation error in media upload - {field}: {field_errors}", extra={'user_id': request.user.id})
            
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
    
    logger.warning("Invalid request method for media upload", extra={'user_id': request.user.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def delete_media(request, media_id):
    """Delete a media file"""
    try:
        media = get_object_or_404(Media, id=media_id, user=request.user)
    except:
        logger.warning(f"Delete attempt on non-existent or unauthorized media: {media_id}", extra={'user_id': request.user.id})
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Media not found'}, status=404)
        messages.error(request, 'Media not found or you do not have permission to delete it.')
        return redirect('user_profile', username=request.user.username)
    
    if request.method == 'POST':
        try:
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                media.delete_file()
                media.delete()
                logger.info(f"Media deleted: {media_id}", extra={'user_id': request.user.id})
                return JsonResponse({'success': True})
            
            # Regular request
            media.delete_file()
            media.delete()
            logger.info(f"Media deleted: {media_id}", extra={'user_id': request.user.id})
            messages.success(request, 'Media deleted successfully!')
            return redirect('user_profile', username=request.user.username)
        except Exception as e:
            logger.error(f"Error deleting media {media_id}: {str(e)}", exc_info=True, extra={'user_id': request.user.id})
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'An error occurred while deleting the media'}, status=500)
            messages.error(request, 'An error occurred while deleting the media. Please try again.')
            return redirect('user_profile', username=request.user.username)
    
    logger.warning("Invalid request method for delete media", extra={'user_id': request.user.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def get_user_media(request):
    """Get all media files for the current user (AJAX endpoint)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        media_files = Media.objects.filter(user=request.user).values(
            'id', 'file', 'thumbnail', 'file_size', 'width', 'height', 'uploaded_at'
        )
        
        media_list = []
        for media in media_files:
            media_list.append({
                'id': media['id'],
                'url': media['file'],
                'thumbnail_url': media['thumbnail'] or media['file'],
                'file_size': media['file_size'],
                'width': media['width'],
                'height': media['height'],
                'uploaded_at': media['uploaded_at'].isoformat() if media['uploaded_at'] else None,
            })
        
        return JsonResponse({
            'success': True,
            'media': media_list
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def get_media_tweets(request, media_id):
    """Get all tweets associated with a media file (AJAX endpoint)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            media = Media.objects.get(id=media_id, user=request.user)
        except Media.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Media not found'}, status=404)
        
        # Get all tweets that use this media
        tweets = media.tweets.all().order_by('-created_at')
        
        tweets_list = []
        for tweet in tweets:
            tweets_list.append({
                'id': tweet.id,
                'text': tweet.text,
                'username': tweet.user.username,
                'created_at': tweet.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'tweets': tweets_list,
            'count': len(tweets_list)
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def get_tweet_edit_history(request, tweet_id):
    """Get edit history for a tweet (AJAX endpoint)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            tweet = Tweet.objects.get(id=tweet_id)
        except Tweet.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tweet not found'}, status=404)
        
        # Get all edit history records for this tweet
        edits = TweetEditHistory.objects.filter(tweet=tweet).order_by('-edited_at')
        
        edit_list = []
        for edit in edits:
            edit_list.append({
                'id': edit.id,
                'previous_content': edit.previous_content,
                'edited_at': edit.edited_at.isoformat(),
                'edited_by': edit.edited_by.username,
                'time_ago': timezone.now() - edit.edited_at
            })
        
        return JsonResponse({
            'success': True,
            'edits': edit_list,
            'edit_count': edits.count()
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@handle_search_error
def search(request):
    """Comprehensive search across tweets and users"""
    query = request.GET.get('q', '').strip()
    page_num = request.GET.get('page', 1)
    
    tweets = []
    users = []
    total_results = 0
    error_message = None
    
    try:
        if query:
            # Validate search query
            validate_search_query(query)
            
            try:
                # Search tweets by content with query optimization
                tweet_results = Tweet.objects.select_related('user', 'user__profile').prefetch_related(
                    'likes', 'comments', 'media'
                ).filter(
                    Q(text__icontains=query)
                ).order_by('-created_at').annotate(
                    like_count=Count('likes')
                )
                
                # Search users by username and bio with query optimization
                user_results = User.objects.select_related('profile').filter(
                    Q(username__icontains=query) |
                    Q(profile__bio__icontains=query) |
                    Q(first_name__icontains=query)
                ).order_by('username').distinct()
                
                # Add user_has_liked flag for authenticated users
                if request.user.is_authenticated:
                    for tweet in tweet_results:
                        tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
                
                # Combine and paginate results
                total_results = tweet_results.count() + user_results.count()
                
                # Paginate tweets (5 per page)
                tweet_paginator = Paginator(tweet_results, 5)
                tweet_page = tweet_paginator.get_page(page_num)
                tweets = tweet_page.object_list
                
                # Paginate users (5 per page)
                user_paginator = Paginator(user_results, 5)
                user_page = user_paginator.get_page(page_num)
                users = user_page.object_list
                
                # Get follow status for each user if authenticated
                if request.user.is_authenticated:
                    for user in users:
                        follow_request = Follow.objects.filter(follower=request.user, following=user).first()
                        if follow_request:
                            user.follow_status = 'accepted' if follow_request.is_accepted else 'pending'
                        else:
                            user.follow_status = 'none'
                
                # Log the search
                log_search_query(request.user, query, total_results)
                
            except Exception as e:
                logger.error(f"Database error during search: {str(e)}", exc_info=True, extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'query': query
                })
                error_message = 'An error occurred while searching. Please try again.'
                messages.error(request, error_message)
    
    except SearchError as e:
        logger.warning(f"Search validation error: {e.message}", extra={
            'user_id': request.user.id if request.user.is_authenticated else None,
            'query': query
        })
        error_message = e.user_message
        messages.error(request, error_message)
    except Exception as e:
        logger.error(f"Unexpected error in search: {str(e)}", exc_info=True, extra={
            'user_id': request.user.id if request.user.is_authenticated else None,
            'query': query
        })
        error_message = 'An unexpected error occurred. Please try again.'
        messages.error(request, error_message)
    
    context = {
        'query': query,
        'tweets': tweets,
        'users': users,
        'total_results': total_results,
        'page_num': page_num,
        'error_message': error_message,
    }
    
    return render(request, 'search_results.html', context)


# Draft management views
@login_required(login_url='login')
def save_draft(request):
    """AJAX endpoint to save tweet draft"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            media_ids = data.get('media_ids', [])
            
            if not content:
                logger.warning("Draft save attempt with empty content", extra={'user_id': request.user.id})
                return JsonResponse({
                    'success': False,
                    'error': 'Draft content cannot be empty'
                }, status=400)
            
            # Get or create draft for this user
            draft, created = TweetDraft.objects.get_or_create(user=request.user)
            
            # Update draft content
            draft.content = content
            draft.save()
            
            # Update associated media
            draft.media.clear()
            if media_ids:
                # Validate that all media belongs to the user
                media_objects = Media.objects.filter(id__in=media_ids, user=request.user)
                draft.media.set(media_objects)
            
            logger.info(f"Draft saved: {draft.id}", extra={
                'user_id': request.user.id,
                'draft_id': draft.id,
                'content_length': len(content),
                'media_count': len(media_ids)
            })
            
            return JsonResponse({
                'success': True,
                'draft_id': draft.id,
                'message': 'Draft saved successfully',
                'updated_at': draft.updated_at.isoformat()
            })
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in draft save request", extra={'user_id': request.user.id})
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format. Please try again.'
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving draft: {str(e)}", exc_info=True, extra={'user_id': request.user.id})
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while saving the draft. Please try again.'
            }, status=500)
    
    logger.warning("Invalid request method for draft save", extra={'user_id': request.user.id})
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)


@login_required(login_url='login')
def get_draft(request):
    """AJAX endpoint to retrieve user's draft"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            draft = TweetDraft.objects.filter(user=request.user).first()
            
            if draft:
                media_list = []
                for media in draft.media.all():
                    media_list.append({
                        'id': media.id,
                        'url': media.file.url,
                        'thumbnail_url': media.thumbnail.url if media.thumbnail else media.file.url,
                    })
                
                return JsonResponse({
                    'success': True,
                    'draft': {
                        'id': draft.id,
                        'content': draft.content,
                        'media': media_list,
                        'updated_at': draft.updated_at.isoformat(),
                        'created_at': draft.created_at.isoformat()
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No draft found'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)


@login_required(login_url='login')
def clear_draft(request):
    """AJAX endpoint to clear user's draft"""
    if request.method == 'POST':
        try:
            draft = TweetDraft.objects.filter(user=request.user).first()
            
            if draft:
                draft.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Draft cleared successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No draft found'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)


@login_required(login_url='login')
def restore_draft(request):
    """AJAX endpoint to restore draft to form"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            draft = TweetDraft.objects.filter(user=request.user).first()
            
            if draft and draft.content:
                media_list = []
                for media in draft.media.all():
                    media_list.append({
                        'id': media.id,
                        'url': media.file.url,
                        'thumbnail_url': media.thumbnail.url if media.thumbnail else media.file.url,
                        'file_size': media.file_size,
                        'width': media.width,
                        'height': media.height,
                    })
                
                return JsonResponse({
                    'success': True,
                    'draft': {
                        'content': draft.content,
                        'media': media_list,
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No draft available'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)


@login_required(login_url='login')
def get_scheduled_tweets(request):
    """AJAX endpoint to get user's scheduled tweets"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            scheduled_tweets = Tweet.objects.filter(
                user=request.user,
                is_scheduled=True,
                scheduled_publish_time__isnull=False
            ).order_by('scheduled_publish_time')
            
            tweets_list = []
            for tweet in scheduled_tweets:
                tweets_list.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'scheduled_publish_time': tweet.scheduled_publish_time.isoformat(),
                    'created_at': tweet.created_at.isoformat(),
                })
            
            return JsonResponse({
                'success': True,
                'scheduled_tweets': tweets_list,
                'count': len(tweets_list)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)


@login_required(login_url='login')
def cancel_scheduled_tweet(request, tweet_id):
    """Cancel a scheduled tweet"""
    try:
        tweet = Tweet.objects.get(pk=tweet_id, user=request.user, is_scheduled=True)
    except Tweet.DoesNotExist:
        logger.warning(f"Cancel attempt on non-existent or unauthorized scheduled tweet: {tweet_id}", extra={'user_id': request.user.id})
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Tweet not found or is not scheduled'}, status=404)
        messages.error(request, 'Tweet not found or you do not have permission to cancel it.')
        return redirect('user_profile', username=request.user.username)
    
    if request.method == 'POST':
        try:
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                tweet.is_scheduled = False
                tweet.scheduled_publish_time = None
                tweet.save()
                
                logger.info(f"Scheduled tweet cancelled: {tweet_id}", extra={'user_id': request.user.id})
                return JsonResponse({'success': True, 'message': 'Scheduled tweet cancelled'})
            
            # Regular request
            tweet.is_scheduled = False
            tweet.scheduled_publish_time = None
            tweet.save()
            
            logger.info(f"Scheduled tweet cancelled: {tweet_id}", extra={'user_id': request.user.id})
            messages.success(request, 'Scheduled tweet cancelled!')
            return redirect('user_profile', username=request.user.username)
        except Exception as e:
            logger.error(f"Error cancelling scheduled tweet {tweet_id}: {str(e)}", exc_info=True, extra={'user_id': request.user.id})
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'An error occurred while cancelling the tweet'}, status=500)
            messages.error(request, 'An error occurred while cancelling the tweet. Please try again.')
            return redirect('user_profile', username=request.user.username)
    
    logger.warning("Invalid request method for cancel scheduled tweet", extra={'user_id': request.user.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def publish_scheduled_tweets_manual(request):
    """Manually trigger publishing of scheduled tweets (for testing/admin)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        # Get all scheduled tweets that are ready to publish
        now = timezone.now()
        tweets_to_publish = Tweet.objects.filter(
            is_scheduled=True,
            scheduled_publish_time__lte=now
        )
        
        count = 0
        for tweet in tweets_to_publish:
            tweet.publish_if_scheduled()
            count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Published {count} scheduled tweets',
            'count': count
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
