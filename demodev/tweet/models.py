from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image
from io import BytesIO
import os




class UserProfile(models.Model):
    """Extended user profile with bio, display name, and profile picture"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.CharField(max_length=500, blank=True, default='')
    display_name = models.CharField(max_length=100, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    def get_follower_count(self):
        return self.user.followers.filter(is_accepted=True).count()

    def get_following_count(self):
        return self.user.following.filter(is_accepted=True).count()

    def get_tweet_count(self):
        return self.user.tweet_set.count()

    def get_display_name(self):
        return self.display_name or self.user.first_name or self.user.username


class Media(models.Model):
    """Media files (images/videos) uploaded by users"""
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='media/%Y/%m/%d/')
    file_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='image')
    file_size = models.IntegerField()  # in bytes
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.user.username} - {self.file_type}'

    def delete_file(self):
        """Delete the media file and thumbnail from storage"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
            self.file.delete(save=False)
        if self.thumbnail:
            if os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)
            self.thumbnail.delete(save=False)

    def save(self, *args, **kwargs):
        """Override save to calculate file size and generate thumbnail"""
        if self.file:
            self.file_size = self.file.size
            # Generate thumbnail for images
            if self.file_type == 'image':
                self.generate_thumbnail()
        super().save(*args, **kwargs)

    def generate_thumbnail(self):
        """Generate a thumbnail for image media"""
        if self.file_type == 'image' and self.file:
            try:
                from django.core.files.base import ContentFile
                
                img = Image.open(self.file)
                self.width = img.width
                self.height = img.height
                
                # Create thumbnail
                img.thumbnail((200, 200))
                thumb_io = BytesIO()
                img.save(thumb_io, format='JPEG')
                thumb_io.seek(0)
                
                # Generate thumbnail filename
                thumb_name = f'thumb_{self.file.name.split("/")[-1]}'
                
                # Save thumbnail using Django's file storage
                self.thumbnail.save(thumb_name, ContentFile(thumb_io.getvalue()), save=False)
            except Exception as e:
                print(f'Error generating thumbnail: {e}')


class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=240)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    media = models.ManyToManyField(Media, blank=True, related_name='tweets')
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}-{self.text[:10]}'

    def mark_as_edited(self):
        """Mark tweet as edited and record the edit time"""
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()

    def pin(self):
        """Pin this tweet to the user's profile"""
        # Unpin any other pinned tweets from this user
        Tweet.objects.filter(user=self.user, is_pinned=True).update(
            is_pinned=False,
            pinned_at=None
        )
        # Pin this tweet
        self.is_pinned = True
        self.pinned_at = timezone.now()
        self.save()

    def unpin(self):
        """Unpin this tweet from the user's profile"""
        self.is_pinned = False
        self.pinned_at = None
        self.save()

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        status = "accepted" if self.is_accepted else "pending"
        return f'{self.follower.username} -> {self.following.username} ({status})'

class Comment(models.Model):
    tweet = models.ForeignKey(Tweet, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} on {self.tweet.text[:20]}'

class TweetEditHistory(models.Model):
    """Track edit history for tweets"""
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='edit_history')
    previous_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-edited_at']

    def __str__(self):
        return f'Edit of {self.tweet.id} by {self.edited_by.username}'


class TweetDraft(models.Model):
    """Store draft tweets for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drafts')
    content = models.TextField(blank=True, default='')
    media = models.ManyToManyField(Media, blank=True, related_name='drafts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Draft by {self.user.username}'


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tweet')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} likes {self.tweet.text[:20]}'




# Signals to auto-create UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(models.signals.pre_delete, sender=Tweet)
def delete_tweet_media(sender, instance, **kwargs):
    """Delete associated media files when a tweet is deleted"""
    # Get all media associated with this tweet before deletion
    media_files = list(instance.media.all())
    
    # Delete each media file
    for media in media_files:
        # Delete the media files from storage
        media.delete_file()
        # Delete the media object from database
        media.delete()


# ============================================================================
# PHASE 2: SOCIAL ENGAGEMENT & DISCOVERY MODELS
# ============================================================================

class Retweet(models.Model):
    """Track retweets of tweets by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='retweets')
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='retweets')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tweet')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['tweet', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} retweeted {self.tweet.id}'


class Hashtag(models.Model):
    """Track hashtags used in tweets"""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', '-updated_at']

    def __str__(self):
        return f'#{self.name}'

    def increment_usage(self):
        """Increment usage count for trending calculation"""
        self.usage_count += 1
        self.updated_at = timezone.now()
        self.save()


class TweetHashtag(models.Model):
    """Association between tweets and hashtags"""
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='hashtags')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='tweets')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tweet', 'hashtag')
        indexes = [
            models.Index(fields=['hashtag', '-created_at']),
        ]

    def __str__(self):
        return f'{self.tweet.id} - {self.hashtag.name}'


class Mention(models.Model):
    """Track mentions of users in tweets"""
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='mentions')
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tweet', 'mentioned_user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentioned_user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.tweet.user.username} mentioned {self.mentioned_user.username}'


class Notification(models.Model):
    """User notifications for interactions"""
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('retweet', 'Retweet'),
        ('mention', 'Mention'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sent', null=True, blank=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'Notification for {self.user.username}: {self.notification_type}'

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    like_notifications = models.BooleanField(default=True)
    retweet_notifications = models.BooleanField(default=True)
    mention_notifications = models.BooleanField(default=True)
    comment_notifications = models.BooleanField(default=True)
    follow_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Notification preferences for {self.user.username}'


class Bookmark(models.Model):
    """User bookmarks for saving tweets"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tweet')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} bookmarked {self.tweet.id}'


class MutedUser(models.Model):
    """Track muted users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='muted_users')
    muted_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='muted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'muted_user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'muted_user']),
        ]

    def __str__(self):
        return f'{self.user.username} muted {self.muted_user.username}'


class BlockedUser(models.Model):
    """Track blocked users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'blocked_user']),
        ]

    def __str__(self):
        return f'{self.user.username} blocked {self.blocked_user.username}'


class TweetAnalytics(models.Model):
    """Track engagement analytics for tweets"""
    tweet = models.OneToOneField(Tweet, on_delete=models.CASCADE, related_name='analytics')
    likes_count = models.IntegerField(default=0)
    retweets_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    bookmarks_count = models.IntegerField(default=0)
    impressions_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Analytics for tweet {self.tweet.id}'

    def update_counts(self):
        """Update all engagement counts from related objects"""
        self.likes_count = self.tweet.likes.count()
        self.retweets_count = self.tweet.retweets.count()
        self.comments_count = self.tweet.comments.count()
        self.bookmarks_count = self.tweet.bookmarks.count()
        self.updated_at = timezone.now()
        self.save()


# ============================================================================
# SIGNAL HANDLERS FOR PHASE 2 MODELS
# ============================================================================

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Auto-create NotificationPreference when a new User is created"""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=Tweet)
def create_tweet_analytics(sender, instance, created, **kwargs):
    """Auto-create TweetAnalytics when a new Tweet is created"""
    if created:
        TweetAnalytics.objects.get_or_create(tweet=instance)


@receiver(post_save, sender=Like)
def update_analytics_on_like(sender, instance, created, **kwargs):
    """Update analytics when a tweet is liked"""
    if created:
        try:
            analytics = instance.tweet.analytics
            analytics.likes_count = instance.tweet.likes.count()
            analytics.updated_at = timezone.now()
            analytics.save()
        except TweetAnalytics.DoesNotExist:
            pass


@receiver(post_save, sender=Retweet)
def update_analytics_on_retweet(sender, instance, created, **kwargs):
    """Update analytics when a tweet is retweeted"""
    if created:
        try:
            analytics = instance.tweet.analytics
            analytics.retweets_count = instance.tweet.retweets.count()
            analytics.updated_at = timezone.now()
            analytics.save()
        except TweetAnalytics.DoesNotExist:
            pass


@receiver(post_save, sender=Comment)
def update_analytics_on_comment(sender, instance, created, **kwargs):
    """Update analytics when a tweet is commented on"""
    if created:
        try:
            analytics = instance.tweet.analytics
            analytics.comments_count = instance.tweet.comments.count()
            analytics.updated_at = timezone.now()
            analytics.save()
        except TweetAnalytics.DoesNotExist:
            pass


@receiver(post_save, sender=Bookmark)
def update_analytics_on_bookmark(sender, instance, created, **kwargs):
    """Update analytics when a tweet is bookmarked"""
    if created:
        try:
            analytics = instance.tweet.analytics
            analytics.bookmarks_count = instance.tweet.bookmarks.count()
            analytics.updated_at = timezone.now()
            analytics.save()
        except TweetAnalytics.DoesNotExist:
            pass
