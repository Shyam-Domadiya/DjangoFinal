# Design Document - Twitter Phase 1: Core Features

## Overview

Phase 1 introduces essential features to transform the basic tweet application into a more complete social platform. The design focuses on:

- **User Profile Enhancement**: Rich user profiles with customizable information and statistics
- **Media Management**: Robust image upload, storage, and display system
- **Content Management**: Tweet editing capabilities with edit history tracking
- **Discovery**: Powerful search across tweets, users, and content
- **Content Planning**: Draft and scheduling features for better content management

The architecture maintains backward compatibility with existing features while adding new capabilities through modular components.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Profile UI  │  Media Upload  │  Search  │  Draft Manager   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                     API Layer                                │
├─────────────────────────────────────────────────────────────┤
│  Profile API  │  Media API  │  Search API  │  Draft API     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Business Logic                             │
├─────────────────────────────────────────────────────────────┤
│  Profile Service  │  Media Service  │  Search Service      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Data Layer                                 │
├─────────────────────────────────────────────────────────────┤
│  Database  │  File Storage  │  Cache Layer                  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Django 4.x with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **File Storage**: Django FileField with local storage (development) / S3 (production)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla + Bootstrap 5)
- **Search**: Django ORM with full-text search capabilities
- **Caching**: Django cache framework

## Components and Interfaces

### 1. User Profile Component

**Responsibilities:**
- Display user information and statistics
- Manage profile editing
- Handle profile picture uploads
- Display user's tweet history

**Key Methods:**
- `get_user_profile(user_id)` - Retrieve user profile data
- `update_user_profile(user_id, data)` - Update profile information
- `upload_profile_picture(user_id, file)` - Handle profile picture upload
- `get_user_statistics(user_id)` - Calculate user stats (tweets, followers, following)

### 2. Media Management Component

**Responsibilities:**
- Handle image uploads and validation
- Store media files securely
- Generate thumbnails
- Manage media lifecycle

**Key Methods:**
- `validate_media_file(file)` - Validate file type and size
- `upload_media(file, user_id)` - Store media and return reference
- `delete_media(media_id)` - Remove media file
- `get_media_url(media_id)` - Retrieve media URL

### 3. Tweet Editing Component

**Responsibilities:**
- Manage tweet edit history
- Validate edited content
- Preserve engagement metrics
- Display edit indicators

**Key Methods:**
- `edit_tweet(tweet_id, new_content, media_ids)` - Update tweet
- `get_tweet_edit_history(tweet_id)` - Retrieve edit history
- `validate_tweet_content(content)` - Validate tweet text

### 4. Search Component

**Responsibilities:**
- Index searchable content
- Execute search queries
- Rank results by relevance
- Handle pagination

**Key Methods:**
- `search_tweets(query, page)` - Search tweet content
- `search_users(query, page)` - Search user profiles
- `search_all(query, page)` - Combined search
- `get_search_suggestions(partial_query)` - Autocomplete suggestions

### 5. Draft Management Component

**Responsibilities:**
- Save draft content to local storage
- Restore drafts on page load
- Clear drafts after publishing
- Manage draft lifecycle

**Key Methods:**
- `save_draft(content, media_ids)` - Store draft locally
- `restore_draft()` - Retrieve saved draft
- `clear_draft()` - Remove draft
- `auto_save_draft()` - Periodic auto-save

### 6. Tweet Scheduling Component

**Responsibilities:**
- Store scheduled tweets
- Execute scheduled publishing
- Manage scheduled tweet lifecycle
- Handle timezone conversions

**Key Methods:**
- `schedule_tweet(content, media_ids, publish_time)` - Create scheduled tweet
- `publish_scheduled_tweets()` - Background job to publish
- `cancel_scheduled_tweet(tweet_id)` - Cancel scheduling
- `get_scheduled_tweets(user_id)` - List user's scheduled tweets

## Data Models

### Extended User Model

```python
class UserProfile(models.Model):
    user = OneToOneField(User, on_delete=CASCADE)
    bio = CharField(max_length=500, blank=True)
    profile_picture = ImageField(upload_to='profile_pictures/', null=True, blank=True)
    display_name = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    def get_follower_count(self):
        return self.user.followers.count()
    
    def get_following_count(self):
        return self.user.following.count()
    
    def get_tweet_count(self):
        return self.user.tweets.count()
```

### Media Model

```python
class Media(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    file = FileField(upload_to='media/%Y/%m/%d/')
    file_type = CharField(max_length=20)  # 'image', 'video'
    file_size = IntegerField()
    width = IntegerField(null=True)
    height = IntegerField(null=True)
    thumbnail = ImageField(upload_to='thumbnails/', null=True)
    uploaded_at = DateTimeField(auto_now_add=True)
    
    def delete_file(self):
        if self.file:
            self.file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
```

### Extended Tweet Model

```python
class Tweet(models.Model):
    # ... existing fields ...
    media = ManyToManyField(Media, blank=True)
    is_edited = BooleanField(default=False)
    edited_at = DateTimeField(null=True, blank=True)
    is_scheduled = BooleanField(default=False)
    scheduled_publish_time = DateTimeField(null=True, blank=True)
    
    def mark_as_edited(self):
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()
```

### Tweet Edit History Model

```python
class TweetEditHistory(models.Model):
    tweet = ForeignKey(Tweet, on_delete=CASCADE)
    previous_content = TextField()
    edited_at = DateTimeField(auto_now_add=True)
    edited_by = ForeignKey(User, on_delete=CASCADE)
    
    class Meta:
        ordering = ['-edited_at']
```

### Draft Model

```python
class TweetDraft(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    content = TextField()
    media = ManyToManyField(Media, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Profile Picture Persistence
*For any* user profile update with a new profile picture, the picture should be stored and retrievable from the same URL across all subsequent page loads.
**Validates: Requirements 1.4**

### Property 2: Media File Validation
*For any* file upload attempt, files exceeding 5MB or with invalid types (not JPEG/PNG/GIF) should be rejected with an appropriate error message.
**Validates: Requirements 2.2**

### Property 3: Media Deletion Cascade
*For any* tweet deletion, all associated media files should be removed from storage and the database.
**Validates: Requirements 2.5**

### Property 4: Tweet Edit Preservation
*For any* edited tweet, the engagement metrics (likes, comments, retweets) should remain unchanged after editing.
**Validates: Requirements 3.5**

### Property 5: Edit History Accuracy
*For any* tweet edit, the previous content should be stored in edit history with the correct timestamp and user information.
**Validates: Requirements 3.4**

### Property 6: Search Result Relevance
*For any* search query, all returned results should contain the search term in tweet content, username, or bio.
**Validates: Requirements 4.1**

### Property 7: Draft Auto-Save Consistency
*For any* draft auto-save operation, the saved content should match the current form state exactly.
**Validates: Requirements 5.1**

### Property 8: Draft Restoration Accuracy
*For any* restored draft, the content and media should match the previously saved state.
**Validates: Requirements 5.3**

### Property 9: Scheduled Tweet Publishing
*For any* scheduled tweet, when the scheduled time arrives, the tweet should be automatically published with the correct content and media.
**Validates: Requirements 6.4**

### Property 10: Media Gallery Consistency
*For any* media item in the gallery, clicking on it should display the correct image and associated tweets.
**Validates: Requirements 7.2**

## Error Handling

### Media Upload Errors
- File too large: Return 413 Payload Too Large with user-friendly message
- Invalid file type: Return 400 Bad Request with supported formats list
- Storage failure: Return 500 Internal Server Error with retry option

### Search Errors
- Empty query: Return empty results with suggestion to enter search term
- Database connection error: Return 503 Service Unavailable
- Timeout on large queries: Implement pagination and timeout handling

### Tweet Editing Errors
- Tweet not found: Return 404 Not Found
- Unauthorized edit attempt: Return 403 Forbidden
- Concurrent edit conflict: Return 409 Conflict with latest version

### Scheduling Errors
- Past timestamp: Return 400 Bad Request with validation message
- Invalid timezone: Return 400 Bad Request with timezone list
- Scheduling service failure: Queue for retry with exponential backoff

## Testing Strategy

### Unit Testing
- Profile picture upload and retrieval
- Media file validation (size, type, dimensions)
- Tweet edit history creation and retrieval
- Search query parsing and result ranking
- Draft save/restore functionality
- Scheduled tweet publishing logic

### Property-Based Testing
- Media validation accepts all valid formats and rejects all invalid ones
- Edit history preserves engagement metrics across all tweet types
- Search results always contain the query term
- Draft restoration produces identical content to saved state
- Scheduled tweets publish at exact scheduled time
- Media gallery displays all uploaded media consistently

### Integration Testing
- End-to-end profile update workflow
- Media upload with tweet creation
- Tweet editing with comment preservation
- Search across multiple content types
- Draft to published tweet workflow
- Scheduled tweet publishing with notifications

### Test Framework
- **Unit Tests**: Django TestCase with pytest
- **Property Tests**: Hypothesis for Python with 100+ iterations per property
- **Integration Tests**: Django Client with fixtures

