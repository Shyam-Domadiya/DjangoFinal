from django.contrib import admin

from .models import Tweet, Follow, Comment, Like, UserProfile, Media, TweetEditHistory, TweetDraft

# Register your models here.
admin.site.register(Tweet)
admin.site.register(Follow)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(UserProfile)
admin.site.register(Media)
admin.site.register(TweetEditHistory)
admin.site.register(TweetDraft)