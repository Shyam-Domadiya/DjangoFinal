from django.shortcuts import redirect, render, get_object_or_404
from .models import Tweet, Follow
from .forms import TweetForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.models import User

def index(request):
    tweets = Tweet.objects.all().order_by('-created_at')
    return render(request, "index.html", {'tweets': tweets})

def tweet_List(request):
    tweets = Tweet.objects.all().order_by('-created_at')
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
        messages.error(request, 'Tweet not found or you do not have permission to delete it.')
        return redirect('tweet_list')
    
    if request.method == "POST":
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

@login_required(login_url='login')
def send_follow_request(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if user_to_follow == request.user:
        messages.error(request, 'You cannot follow yourself!')
        return redirect('user_list')
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if created:
        messages.success(request, f'Follow request sent to {user_to_follow.username}!')
    else:
        messages.info(request, f'Follow request already sent to {user_to_follow.username}.')
    
    return redirect('user_list')

@login_required(login_url='login')
def accept_follow_request(request, follow_id):
    follow = get_object_or_404(Follow, id=follow_id, following=request.user)
    follow.is_accepted = True
    follow.save()
    messages.success(request, f'You accepted {follow.follower.username}\'s follow request!')
    return redirect('follow_requests')

@login_required(login_url='login')
def reject_follow_request(request, follow_id):
    follow = get_object_or_404(Follow, id=follow_id, following=request.user)
    follow.delete()
    messages.success(request, f'You rejected {follow.follower.username}\'s follow request!')
    return redirect('follow_requests')

@login_required(login_url='login')
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    messages.success(request, f'You unfollowed {user_to_unfollow.username}!')
    return redirect('user_list')

@login_required(login_url='login')
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    
    # Get follow status for each user
    for user in users:
        follow = Follow.objects.filter(follower=request.user, following=user).first()
        user.follow_status = 'none'
        if follow:
            user.follow_status = 'accepted' if follow.is_accepted else 'pending'
    
    return render(request, 'user_list.html', {'users': users})

@login_required(login_url='login')
def follow_requests(request):
    pending_requests = Follow.objects.filter(following=request.user, is_accepted=False)
    return render(request, 'follow_requests.html', {'pending_requests': pending_requests})
