from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    UserProfileViewSet, MediaViewSet, TweetViewSet,
    TweetDraftViewSet, SearchViewSet
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'media', MediaViewSet, basename='media')
router.register(r'tweets', TweetViewSet, basename='tweet')
router.register(r'drafts', TweetDraftViewSet, basename='draft')
router.register(r'search', SearchViewSet, basename='search')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
]
