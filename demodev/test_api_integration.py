"""
Integration tests for REST API endpoints.

These tests verify that all API endpoints work correctly together,
testing the complete workflows for:
- Profile management
- Media upload and management
- Tweet creation, editing, and deletion
- Search functionality
- Draft management
- Tweet scheduling
"""

import json
import os
from io import BytesIO
from PIL import Image

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

from tweet.models import UserProfile, Media, Tweet, TweetEditHistory, TweetDraft, Like, Comment


class ProfileAPIIntegrationTestCase(TestCase):
    """Integration tests for profile API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Ensure profile exists
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.bio = 'Original bio'
        profile.display_name = 'Test User'
        profile.save()

    def test_profile_api_get_all_profiles(self):
        """Test GET /api/profiles/ returns all profiles"""
        response = self.client.get('/api/profiles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, dict) and 'results' in data:
            self.assertGreater(len(data['results']), 0)
        elif isinstance(data, list):
            self.assertGreater(len(data), 0)
        else:
            self.fail("Unexpected response format")

    def test_profile_api_get_current_user_profile(self):
        """Test GET /api/profiles/me/ returns current user profile"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/api/profiles/me/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['bio'], 'Original bio')

    def test_profile_api_get_specific_profile(self):
        """Test GET /api/profiles/{username}/ returns specific profile"""
        response = self.client.get('/api/profiles/testuser/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['user']['username'], 'testuser')

    def test_profile_api_update_own_profile(self):
        """Test PATCH /api/profiles/{username}/ updates own profile"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.patch(
            '/api/profiles/testuser/',
            data=json.dumps({
                'bio': 'Updated bio',
                'display_name': 'Updated Name'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['bio'], 'Updated bio')
        self.assertEqual(data['display_name'], 'Updated Name')

    def test_profile_api_cannot_update_other_profile(self):
        """Test that user cannot update another user's profile"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.patch(
            '/api/profiles/otheruser/',
            data=json.dumps({'bio': 'Hacked bio'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_profile_api_get_statistics(self):
        """Test GET /api/profiles/{username}/statistics/ returns profile stats"""
        response = self.client.get('/api/profiles/testuser/statistics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('follower_count', data)
        self.assertIn('following_count', data)
        self.assertIn('tweet_count', data)


class MediaAPIIntegrationTestCase(TestCase):
    """Integration tests for media API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def create_test_image(self, name='test.jpg', size=(100, 100)):
        """Helper to create a test image"""
        img = Image.new('RGB', size, color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_media_api_upload_image(self):
        """Test POST /api/media/ uploads an image"""
        test_image = self.create_test_image()
        response = self.client.post(
            '/api/media/',
            {'file': test_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('file', data)

    def test_media_api_get_user_media(self):
        """Test GET /api/media/ returns user's media"""
        # Upload a media file
        test_image = self.create_test_image()
        self.client.post('/api/media/', {'file': test_image}, format='multipart')
        
        # Get user's media
        response = self.client.get('/api/media/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, dict) and 'results' in data:
            self.assertEqual(len(data['results']), 1)
        elif isinstance(data, list):
            self.assertEqual(len(data), 1)
        else:
            self.fail("Unexpected response format")

    def test_media_api_get_specific_media(self):
        """Test GET /api/media/{id}/ returns specific media"""
        # Upload a media file
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/media/',
            {'file': test_image},
            format='multipart'
        )
        media_id = upload_response.json()['id']
        
        # Get specific media
        response = self.client.get(f'/api/media/{media_id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], media_id)

    def test_media_api_delete_media(self):
        """Test DELETE /api/media/{id}/ deletes media"""
        # Upload a media file
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/media/',
            {'file': test_image},
            format='multipart'
        )
        media_id = upload_response.json()['id']
        
        # Delete media
        response = self.client.delete(f'/api/media/{media_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify media is deleted
        response = self.client.get(f'/api/media/{media_id}/')
        self.assertEqual(response.status_code, 404)

    def test_media_api_get_tweets_for_media(self):
        """Test GET /api/media/{id}/tweets/ returns tweets using media"""
        # Upload a media file
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/media/',
            {'file': test_image},
            format='multipart'
        )
        media_id = upload_response.json()['id']
        
        # Create a tweet with this media
        tweet = Tweet.objects.create(
            user=self.user,
            text='Tweet with media'
        )
        media = Media.objects.get(id=media_id)
        tweet.media.add(media)
        
        # Get tweets for media
        response = self.client.get(f'/api/media/{media_id}/tweets/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['tweets']), 1)


class TweetAPIIntegrationTestCase(TestCase):
    """Integration tests for tweet API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_tweet_api_create_tweet(self):
        """Test POST /api/tweets/ creates a tweet"""
        response = self.client.post(
            '/api/tweets/',
            data=json.dumps({'text': 'Test tweet'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['text'], 'Test tweet')
        self.assertEqual(data['user']['username'], 'testuser')

    def test_tweet_api_get_tweets(self):
        """Test GET /api/tweets/ returns tweets"""
        # Create a tweet
        Tweet.objects.create(user=self.user, text='Test tweet')
        
        # Get tweets
        response = self.client.get('/api/tweets/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, dict) and 'results' in data:
            self.assertGreater(len(data['results']), 0)
        elif isinstance(data, list):
            self.assertGreater(len(data), 0)
        else:
            self.fail("Unexpected response format")

    def test_tweet_api_get_specific_tweet(self):
        """Test GET /api/tweets/{id}/ returns specific tweet"""
        # Create a tweet
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        
        # Get specific tweet
        response = self.client.get(f'/api/tweets/{tweet.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], tweet.id)
        self.assertEqual(data['text'], 'Test tweet')

    def test_tweet_api_update_tweet(self):
        """Test PATCH /api/tweets/{id}/ updates a tweet"""
        # Create a tweet
        tweet = Tweet.objects.create(user=self.user, text='Original text')
        
        # Update tweet
        response = self.client.patch(
            f'/api/tweets/{tweet.id}/',
            data=json.dumps({'text': 'Updated text'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['text'], 'Updated text')
        self.assertTrue(data['is_edited'])

    def test_tweet_api_delete_tweet(self):
        """Test DELETE /api/tweets/{id}/ deletes a tweet"""
        # Create a tweet
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        tweet_id = tweet.id
        
        # Delete tweet
        response = self.client.delete(f'/api/tweets/{tweet_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify tweet is deleted
        self.assertFalse(Tweet.objects.filter(id=tweet_id).exists())

    def test_tweet_api_like_tweet(self):
        """Test POST /api/tweets/{id}/like/ likes a tweet"""
        # Create a tweet
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        
        # Like tweet
        response = self.client.post(f'/api/tweets/{tweet.id}/like/')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['liked'])

    def test_tweet_api_unlike_tweet(self):
        """Test POST /api/tweets/{id}/unlike/ unlikes a tweet"""
        # Create a tweet and like it
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        Like.objects.create(user=self.user, tweet=tweet)
        
        # Unlike tweet
        response = self.client.post(f'/api/tweets/{tweet.id}/unlike/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['liked'])

    def test_tweet_api_get_likes(self):
        """Test GET /api/tweets/{id}/likes/ returns likes"""
        # Create a tweet and like it
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        Like.objects.create(user=self.user, tweet=tweet)
        
        # Get likes
        response = self.client.get(f'/api/tweets/{tweet.id}/likes/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_tweet_api_add_comment(self):
        """Test POST /api/tweets/{id}/add_comment/ adds a comment"""
        # Create a tweet
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        
        # Add comment
        response = self.client.post(
            f'/api/tweets/{tweet.id}/add_comment/',
            data=json.dumps({'text': 'Test comment'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['text'], 'Test comment')

    def test_tweet_api_get_comments(self):
        """Test GET /api/tweets/{id}/comments/ returns comments"""
        # Create a tweet and add a comment
        tweet = Tweet.objects.create(user=self.user, text='Test tweet')
        Comment.objects.create(user=self.user, tweet=tweet, text='Test comment')
        
        # Get comments
        response = self.client.get(f'/api/tweets/{tweet.id}/comments/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_tweet_api_get_edit_history(self):
        """Test GET /api/tweets/{id}/edit_history/ returns edit history"""
        # Create a tweet and edit it
        tweet = Tweet.objects.create(user=self.user, text='Original text')
        tweet.text = 'Updated text'
        tweet.save()
        TweetEditHistory.objects.create(
            tweet=tweet,
            previous_content='Original text',
            edited_by=self.user
        )
        
        # Get edit history
        response = self.client.get(f'/api/tweets/{tweet.id}/edit_history/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

class SearchAPIIntegrationTestCase(TestCase):
    """Integration tests for search API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='testpass123'
        )
        self.user1.profile.bio = 'Python developer'
        self.user1.profile.save()
        
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='testpass123'
        )
        
        # Create tweets
        Tweet.objects.create(user=self.user1, text='I love Python programming')
        Tweet.objects.create(user=self.user2, text='JavaScript is great')

    def test_search_api_search_tweets(self):
        """Test GET /api/search/tweets/?q=query searches tweets"""
        response = self.client.get('/api/search/tweets/?q=Python')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0)
        self.assertIn('results', data)

    def test_search_api_search_users(self):
        """Test GET /api/search/users/?q=query searches users"""
        response = self.client.get('/api/search/users/?q=alice')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0)
        self.assertIn('results', data)

    def test_search_api_search_all(self):
        """Test GET /api/search/all/?q=query searches all"""
        response = self.client.get('/api/search/all/?q=Python')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tweets', data)
        self.assertIn('users', data)

    def test_search_api_empty_query_returns_error(self):
        """Test that empty search query returns error"""
        response = self.client.get('/api/search/tweets/?q=')
        self.assertEqual(response.status_code, 400)

    def test_search_api_no_results(self):
        """Test search with no results"""
        response = self.client.get('/api/search/tweets/?q=nonexistent12345')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 0)


class DraftAPIIntegrationTestCase(TestCase):
    """Integration tests for draft API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_draft_api_create_draft(self):
        """Test POST /api/drafts/ creates a draft"""
        response = self.client.post(
            '/api/drafts/',
            data=json.dumps({'content': 'Draft content'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['content'], 'Draft content')

    def test_draft_api_get_current_draft(self):
        """Test GET /api/drafts/current/ returns current draft"""
        # Create a draft
        TweetDraft.objects.create(user=self.user, content='Draft content')
        
        # Get current draft
        response = self.client.get('/api/drafts/current/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['content'], 'Draft content')

    def test_draft_api_update_draft(self):
        """Test PATCH /api/drafts/{id}/ updates a draft"""
        # Create a draft
        draft = TweetDraft.objects.create(user=self.user, content='Original content')
        
        # Update draft
        response = self.client.patch(
            f'/api/drafts/{draft.id}/',
            data=json.dumps({'content': 'Updated content'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['content'], 'Updated content')

    def test_draft_api_delete_draft(self):
        """Test DELETE /api/drafts/{id}/ deletes a draft"""
        # Create a draft
        draft = TweetDraft.objects.create(user=self.user, content='Draft content')
        draft_id = draft.id
        
        # Delete draft
        response = self.client.delete(f'/api/drafts/{draft_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify draft is deleted
        self.assertFalse(TweetDraft.objects.filter(id=draft_id).exists())

    def test_draft_api_clear_draft(self):
        """Test POST /api/drafts/clear/ clears current draft"""
        # Create a draft
        TweetDraft.objects.create(user=self.user, content='Draft content')
        
        # Clear draft
        response = self.client.post('/api/drafts/clear/')
        self.assertEqual(response.status_code, 200)
        
        # Verify draft is deleted
        self.assertFalse(TweetDraft.objects.filter(user=self.user).exists())

    def test_draft_api_no_draft_returns_404(self):
        """Test GET /api/drafts/current/ returns 404 when no draft exists"""
        response = self.client.get('/api/drafts/current/')
        self.assertEqual(response.status_code, 404)


class CompleteWorkflowIntegrationTestCase(TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def create_test_image(self, name='test.jpg'):
        """Helper to create a test image"""
        img = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_complete_tweet_with_media_workflow(self):
        """Test complete workflow: upload media, create tweet with media"""
        # 1. Upload media
        test_image = self.create_test_image()
        media_response = self.client.post(
            '/api/media/',
            {'file': test_image},
            format='multipart'
        )
        self.assertEqual(media_response.status_code, 201)
        media_id = media_response.json()['id']
        
        # 2. Create tweet with media
        tweet_response = self.client.post(
            '/api/tweets/',
            data=json.dumps({
                'text': 'Tweet with media',
                'media_ids': [media_id]
            }),
            content_type='application/json'
        )
        self.assertEqual(tweet_response.status_code, 201)
        tweet_id = tweet_response.json()['id']
        
        # 3. Verify tweet has media
        get_response = self.client.get(f'/api/tweets/{tweet_id}/')
        self.assertEqual(get_response.status_code, 200)
        data = get_response.json()
        self.assertEqual(len(data['media']), 1)

    def test_complete_draft_to_tweet_workflow(self):
        """Test complete workflow: save draft, restore draft, publish tweet"""
        # 1. Save draft
        draft_response = self.client.post(
            '/api/drafts/',
            data=json.dumps({'content': 'Draft content'}),
            content_type='application/json'
        )
        self.assertEqual(draft_response.status_code, 201)
        draft_id = draft_response.json()['id']
        
        # 2. Retrieve draft
        get_response = self.client.get(f'/api/drafts/{draft_id}/')
        self.assertEqual(get_response.status_code, 200)
        draft_data = get_response.json()
        self.assertEqual(draft_data['content'], 'Draft content')
        
        # 3. Create tweet from draft content
        tweet_response = self.client.post(
            '/api/tweets/',
            data=json.dumps({'text': draft_data['content']}),
            content_type='application/json'
        )
        self.assertEqual(tweet_response.status_code, 201)
        
        # 4. Delete draft
        delete_response = self.client.delete(f'/api/drafts/{draft_id}/')
        self.assertEqual(delete_response.status_code, 204)

    def test_complete_tweet_edit_workflow(self):
        """Test complete workflow: create tweet, edit it, view history"""
        # 1. Create tweet
        create_response = self.client.post(
            '/api/tweets/',
            data=json.dumps({'text': 'Original content'}),
            content_type='application/json'
        )
        self.assertEqual(create_response.status_code, 201)
        tweet_id = create_response.json()['id']
        
        # 2. Edit tweet
        edit_response = self.client.patch(
            f'/api/tweets/{tweet_id}/',
            data=json.dumps({'text': 'Updated content'}),
            content_type='application/json'
        )
        self.assertEqual(edit_response.status_code, 200)
        self.assertTrue(edit_response.json()['is_edited'])
        
        # 3. View edit history
        history_response = self.client.get(f'/api/tweets/{tweet_id}/edit_history/')
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(history_response.json()['count'], 1)

    def test_complete_engagement_workflow(self):
        """Test complete workflow: create tweet, like, comment, view engagement"""
        # 1. Create tweet
        create_response = self.client.post(
            '/api/tweets/',
            data=json.dumps({'text': 'Test tweet'}),
            content_type='application/json'
        )
        tweet_id = create_response.json()['id']
        
        # 2. Like tweet
        like_response = self.client.post(f'/api/tweets/{tweet_id}/like/')
        self.assertEqual(like_response.status_code, 201)
        
        # 3. Add comment
        comment_response = self.client.post(
            f'/api/tweets/{tweet_id}/add_comment/',
            data=json.dumps({'text': 'Great tweet!'}),
            content_type='application/json'
        )
        self.assertEqual(comment_response.status_code, 201)
        
        # 4. View tweet with engagement
        get_response = self.client.get(f'/api/tweets/{tweet_id}/')
        data = get_response.json()
        self.assertEqual(data['like_count'], 1)
        self.assertEqual(data['comment_count'], 1)
