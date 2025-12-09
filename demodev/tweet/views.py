from django.shortcuts import redirect, render, get_object_or_404
from .models import Tweet
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
