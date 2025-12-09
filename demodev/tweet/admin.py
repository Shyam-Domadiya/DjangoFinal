from django.contrib import admin

from .models import Tweet, Follow

# Register your models here.
admin.site.register(Tweet)
admin.site.register(Follow)