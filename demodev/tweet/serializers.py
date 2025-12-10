from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Media, Tweet, TweetEditHistory, 
    TweetDraft, Comment, Like, Follow
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    tweet_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'display_name', 'profile_picture',
            'follower_count', 'following_count', 'tweet_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_follower_count(self, obj):
        return obj.get_follower_count()
    
    def get_following_count(self, obj):
        return obj.get_following_count()
    
    def get_tweet_count(self, obj):
        return obj.get_tweet_count()


class MediaSerializer(serializers.ModelSerializer):
    """Serializer for Media model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Media
        fields = [
            'id', 'user', 'file', 'file_type', 'file_size',
            'width', 'height', 'thumbnail', 'uploaded_at'
        ]
        read_only_fields = ['id', 'user', 'file_size', 'width', 'height', 'thumbnail', 'uploaded_at']


class TweetEditHistorySerializer(serializers.ModelSerializer):
    """Serializer for TweetEditHistory model"""
    edited_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TweetEditHistory
        fields = ['id', 'tweet', 'previous_content', 'edited_at', 'edited_by']
        read_only_fields = ['id', 'tweet', 'edited_at', 'edited_by']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'tweet', 'user', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for Like model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'tweet', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class TweetSerializer(serializers.ModelSerializer):
    """Serializer for Tweet model"""
    user = UserSerializer(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    media_ids = serializers.PrimaryKeyRelatedField(
        queryset=Media.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='media'
    )
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Tweet
        fields = [
            'id', 'user', 'text', 'photo', 'media', 'media_ids',
            'is_edited', 'edited_at', 'is_scheduled', 'scheduled_publish_time',
            'is_pinned', 'pinned_at',
            'like_count', 'comment_count', 'user_has_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_edited', 'edited_at', 'is_pinned', 'pinned_at', 'created_at', 'updated_at']
    
    def get_like_count(self, obj):
        return obj.likes.count()
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, tweet=obj).exists()
        return False


class TweetDetailSerializer(TweetSerializer):
    """Extended serializer for tweet detail view with edit history and comments"""
    edit_history = TweetEditHistorySerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta(TweetSerializer.Meta):
        fields = TweetSerializer.Meta.fields + ['edit_history', 'comments']


class TweetDraftSerializer(serializers.ModelSerializer):
    """Serializer for TweetDraft model"""
    user = UserSerializer(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    media_ids = serializers.PrimaryKeyRelatedField(
        queryset=Media.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='media'
    )
    
    class Meta:
        model = TweetDraft
        fields = ['id', 'user', 'content', 'media', 'media_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class FollowSerializer(serializers.ModelSerializer):
    """Serializer for Follow model"""
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'is_accepted', 'created_at']
        read_only_fields = ['id', 'created_at']
