from django.shortcuts import redirect, render, get_object_or_404
from .models import Tweet, Follow, Comment, Like
from .forms import TweetForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone

def index(request):
    tweets = Tweet.objects.all().order_by('-created_at').annotate(
        like_count=Count('likes')
    )
    
    # Add user_has_liked flag for authenticated users
    if request.user.is_authenticated:
        for tweet in tweets:
            tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
    
    return render(request, "index.html", {'tweets': tweets})

def tweet_List(request):
    tweets = Tweet.objects.all().order_by('-created_at').annotate(
        like_count=Count('likes')
    )
    
    # Add user_has_liked flag for authenticated users
    if request.user.is_authenticated:
        for tweet in tweets:
            tweet.user_has_liked = Like.objects.filter(user=request.user, tweet=tweet).exists()
    
    return render(request, 'tweet_list.html', {'tweets': tweets})

@login_required(login_url='login')
def tweet_Create(request):
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            messages.success(request, 'Tweet created successfully!')
            return redirect('tweet_list')
    else:
        form = TweetForm()
    return render(request, 'tweet_form.html', {'form': form})

@login_required(login_url='login')
def Tweet_Edit(request, tweet_id):
    try:
        tweet = Tweet.objects.get(pk=tweet_id, user=request.user)
    except Tweet.DoesNotExist:
        messages.error(request, 'Tweet not found or you do not have permission to edit it.')
        return redirect('tweet_list')
    
    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            messages.success(request, 'Tweet updated successfully!')
            return redirect('tweet_list')
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
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome!')
            return redirect('tweet_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('index')

# Follow/Unfollow functionality
@login_required(login_url='login')
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    
    # Get follow status for each user
    for user in users:
        follow_request = Follow.objects.filter(follower=request.user, following=user).first()
        if follow_request:
            user.follow_status = 'accepted' if follow_request.is_accepted else 'pending'
        else:
            user.follow_status = 'none'
    
    return render(request, 'user_list.html', {'users': users})

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
    pending_requests = Follow.objects.filter(following=request.user, is_accepted=False)
    return render(request, 'follow_requests.html', {'pending_requests': pending_requests})

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
    tweet = get_object_or_404(Tweet, id=tweet_id)
    comments = tweet.comments.all()
    
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
    likes = Like.objects.filter(tweet=tweet).select_related('user')
    return render(request, 'tweet_likes.html', {
        'tweet': tweet,
        'likes': likes
    })

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

