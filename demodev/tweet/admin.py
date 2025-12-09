from django.contrib import admin

from .models import Tweet, Follow, Comment, Like

# Register your models here.
admin.site.register(Tweet)
admin.site.register(Follow)
admin.site.register(Comment)
admin.site.register(Like)