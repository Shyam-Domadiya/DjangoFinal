# Design Document - Twitter Phase 2: Social Engagement & Discovery

## Overview

Phase 2 transforms the platform from a basic tweet-sharing application into a fully-featured social network with rich engagement capabilities. The design focuses on:

- **Social Interactions**: Retweets, mentions, and threaded conversations
- **Content Discovery**: Hashtags, trending topics, and user recommendations
- **User Control**: Muting, blocking, and notification preferences
- **Engagement Tracking**: Analytics and insights for content creators
- **Community Moderation**: Tools for users to manage conversations on their content

The architecture extends Phase 1 components while introducing new services for social graph management, notification handling, and analytics.

## Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend Layer                            │
├──────────────────────────────────────────────────────────────┤
│ Notifications │ Hashtags │ Recommendations │ Analytics │ Mod │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                     API Layer                                 │
├──────────────────────────────────────────────────────────────┤
│ Retweet API │ Hashtag API │ Notification API │ Analytics API │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                   Business Logic                              │
├──────────────────────────────────────────────────────────────┤
│ Social Service │ Notification Service │ Analytics Service    │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                   Data Layer                                  │
├──────────────────────────────────────────────────────────────┤
│ Database │ Cache │ Search Index                              │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Django 4.x with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Caching**: Redis for real-time notifications and trending data
- **Search**: Elasticsearch for hashtag and content indexing
- **Task Queue**: Celery for async notification processing
- **Frontend**: HTML5, CSS3, JavaScript with WebSocket support for real-time updates

## Components and Interfaces

### 1. Retweet Component

**Responsibilities:**
- Manage retweet creation and deletion
- Track retweet counts
- Prevent duplicate retweets
- Notify original tweet authors

**Key Methods:**
- `create_retweet(user_id, tweet_id)` - Create a retweet record
- `delete_retweet(user_id, tweet_id)` - Remove a retweet
- `get_retweet_count(tweet_id)` - Get total retweets for a tweet
- `is_retweeted_by_user(user_id, tweet_id)` - Check if user has retweeted

**Data Model:**
```
Retweet:
  - id (PK)
  - user (FK to User)
  - tweet (FK to Tweet)
  - created_at
  - unique_together(user, tweet)
```

### 2. Hashtag Component

**Responsibilities:**
- Extract and index hashtags from tweets
- Track hashtag usage and trends
- Provide hashtag autocomplete
- Generate trending topics

**Key Methods:**
- `extract_hashtags(text)` - Parse hashtags from tweet text
- `create_hashtag(name)` - Create or retrieve hashtag
- `get_trending_hashtags(limit=10)` - Get trending hashtags
- `search_hashtag(query)` - Search for hashtags with autocomplete
- `get_hashtag_tweets(hashtag_id)` - Get all tweets with hashtag

**Data Model:**
```
Hashtag:
  - id (PK)
  - name (unique)
  - usage_count
  - created_at
  - updated_at

TweetHashtag:
  - id (PK)
  - tweet (FK to Tweet)
  - hashtag (FK to Hashtag)
  - created_at
```

### 3. Mention Component

**Responsibilities:**
- Extract mentions from tweets
- Notify mentioned users
- Provide mention autocomplete
- Track mention history

**Key Methods:**
- `extract_mentions(text)` - Parse @mentions from tweet text
- `create_mention(tweet_id, mentioned_user_id)` - Record a mention
- `get_user_mentions(user_id)` - Get all mentions for a user
- `notify_mentioned_users(tweet_id)` - Send notifications to mentioned users

**Data Model:**
```
Mention:
  - id (PK)
  - tweet (FK to Tweet)
  - mentioned_user (FK to User)
  - created_at
```

### 4. Notification Component

**Responsibilities:**
- Create and manage notifications
- Handle notification delivery
- Track notification read status
- Respect user preferences

**Key Methods:**
- `create_notification(user_id, type, related_object)` - Create notification
- `get_user_notifications(user_id, limit=20)` - Retrieve user's notifications
- `mark_as_read(notification_id)` - Mark notification as read
- `delete_notification(notification_id)` - Delete notification
- `get_unread_count(user_id)` - Get count of unread notifications

**Data Model:**
```
Notification:
  - id (PK)
  - user (FK to User)
  - type (like, retweet, mention, comment, follow)
  - related_object_id
  - related_object_type
  - is_read
  - created_at

NotificationPreference:
  - id (PK)
  - user (FK to User)
  - notification_type
  - is_enabled
```

### 5. Thread Component

**Responsibilities:**
- Manage tweet replies and threads
- Display conversation threads
- Track reply relationships
- Maintain thread integrity

**Key Methods:**
- `create_reply(user_id, text, parent_tweet_id)` - Create a reply tweet
- `get_thread(tweet_id)` - Get all tweets in a thread
- `get_replies(tweet_id)` - Get direct replies to a tweet
- `get_conversation_depth(tweet_id)` - Get thread depth

**Data Model:**
```
Tweet (extended):
  - parent_tweet (FK to Tweet, nullable)
  - reply_count (denormalized)
```

### 6. Bookmark Component

**Responsibilities:**
- Manage user bookmarks
- Retrieve bookmarked tweets
- Track bookmark status
- Provide bookmark management

**Key Methods:**
- `create_bookmark(user_id, tweet_id)` - Bookmark a tweet
- `delete_bookmark(user_id, tweet_id)` - Remove bookmark
- `get_user_bookmarks(user_id)` - Get all bookmarks for user
- `is_bookmarked(user_id, tweet_id)` - Check if tweet is bookmarked

**Data Model:**
```
Bookmark:
  - id (PK)
  - user (FK to User)
  - tweet (FK to Tweet)
  - created_at
  - unique_together(user, tweet)
```

### 7. Mute/Block Component

**Responsibilities:**
- Manage muted and blocked users
- Filter content from muted/blocked users
- Enforce block restrictions
- Maintain relationship integrity

**Key Methods:**
- `mute_user(user_id, muted_user_id)` - Mute a user
- `unmute_user(user_id, muted_user_id)` - Unmute a user
- `block_user(user_id, blocked_user_id)` - Block a user
- `unblock_user(user_id, blocked_user_id)` - Unblock a user
- `is_muted(user_id, target_user_id)` - Check if user is muted
- `is_blocked(user_id, target_user_id)` - Check if user is blocked

**Data Model:**
```
MutedUser:
  - id (PK)
  - user (FK to User)
  - muted_user (FK to User)
  - created_at
  - unique_together(user, muted_user)

BlockedUser:
  - id (PK)
  - user (FK to User)
  - blocked_user (FK to User)
  - created_at
  - unique_together(user, blocked_user)
```

### 8. Analytics Component

**Responsibilities:**
- Track engagement metrics
- Calculate analytics data
- Generate insights and trends
- Provide analytics API

**Key Methods:**
- `get_tweet_analytics(tweet_id)` - Get engagement metrics for a tweet
- `get_user_analytics(user_id)` - Get overall user analytics
- `get_engagement_trend(user_id, days=30)` - Get engagement over time
- `calculate_engagement_rate(tweet_id)` - Calculate engagement percentage

**Data Model:**
```
TweetAnalytics:
  - id (PK)
  - tweet (FK to Tweet)
  - likes_count
  - retweets_count
  - comments_count
  - bookmarks_count
  - impressions_count
  - updated_at
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Retweet Idempotence
*For any* user and tweet, retweeting the same tweet multiple times without undoing should result in only one retweet record existing.
**Validates: Requirements 1.2, 1.5**

### Property 2: Hashtag Extraction Completeness
*For any* tweet text containing hashtags, all hashtags should be extracted and indexed, regardless of their position or quantity in the text.
**Validates: Requirements 2.2**

### Property 3: Mention Notification Delivery
*For any* tweet containing mentions, all mentioned users should receive a notification, and only mentioned users should receive mention notifications.
**Validates: Requirements 3.2, 3.3**

### Property 4: Thread Integrity
*For any* tweet that is a reply, the parent-child relationship should be preserved, and traversing the thread should return all connected tweets in correct order.
**Validates: Requirements 4.2, 4.4**

### Property 5: Bookmark Persistence
*For any* bookmarked tweet, the bookmark should persist until explicitly removed, and the tweet should appear in the user's bookmarks collection.
**Validates: Requirements 5.2, 5.3**

### Property 6: Block Enforcement
*For any* blocked user, they should be unable to view the blocking user's profile, tweets, or interact with their content.
**Validates: Requirements 6.3, 6.4**

### Property 7: Notification Preference Respect
*For any* disabled notification type, no notifications of that type should be sent to the user, regardless of triggering events.
**Validates: Requirements 7.2, 7.4**

### Property 8: Analytics Accuracy
*For any* tweet, the engagement metrics in analytics should match the actual count of likes, retweets, comments, and bookmarks.
**Validates: Requirements 9.2, 9.3**

### Property 9: Mute Filtering
*For any* muted user, their tweets should not appear in the muting user's timeline, but should still be accessible if directly navigated to.
**Validates: Requirements 6.2**

### Property 10: Mention Extraction Accuracy
*For any* tweet text containing @mentions, all valid mentions should be extracted and only valid usernames should be recognized.
**Validates: Requirements 3.1**

## Error Handling

- **Invalid Retweet**: Return 400 error if user tries to retweet their own tweet
- **Duplicate Retweet**: Return 409 error if user tries to retweet already retweeted tweet
- **Invalid Mention**: Return 400 error if mentioned user doesn't exist
- **Block Violation**: Return 403 error if blocked user tries to interact
- **Notification Delivery**: Log failures and retry with exponential backoff
- **Analytics Calculation**: Cache results and update asynchronously

## Testing Strategy

### Unit Testing
- Test hashtag extraction with various text patterns
- Test mention parsing with edge cases
- Test retweet creation and deletion
- Test bookmark operations
- Test mute/block enforcement
- Test notification creation and filtering

### Property-Based Testing
- Generate random tweets with hashtags and verify extraction
- Generate random user interactions and verify notification delivery
- Generate random thread structures and verify integrity
- Generate random mute/block combinations and verify filtering
- Generate random analytics data and verify accuracy

### Integration Testing
- Test end-to-end retweet workflow
- Test notification delivery across multiple users
- Test thread creation and display
- Test analytics calculation with real data
- Test mute/block with actual user interactions

