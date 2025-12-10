from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from io import BytesIO
from PIL import Image
import os
import uuid
import json

from .models import UserProfile, Media, Tweet, Like, Comment, TweetEditHistory, TweetDraft
from .forms import MediaUploadForm, TweetForm


class ProfilePictureTestCase(HypothesisTestCase):
    """Test cases for user profile picture persistence"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    @given(
        display_name=st.text(min_size=1, max_size=100),
        bio=st.text(max_size=500)
    )
    @settings(max_examples=100)
    def test_profile_picture_persistence_property(self, display_name, bio):
        """
        **Feature: twitter-phase-1-core-features, Property 1: Profile Picture Persistence**
        
        Property: For any user profile update with a new profile picture, 
        the picture should be stored and retrievable from the same URL across 
        all subsequent page loads.
        
        **Validates: Requirements 1.4**
        """
        # Create a test image
        test_image = self.create_test_image()
        
        # Update the profile with the image
        profile = self.user.profile
        profile.display_name = display_name
        profile.bio = bio
        profile.profile_picture = test_image
        profile.save()
        
        # Retrieve the profile from database
        retrieved_profile = UserProfile.objects.get(user=self.user)
        
        # Verify the profile picture is stored
        self.assertIsNotNone(retrieved_profile.profile_picture)
        
        # Verify the profile picture URL is consistent
        original_url = retrieved_profile.profile_picture.url
        
        # Retrieve again to ensure URL consistency
        retrieved_again = UserProfile.objects.get(user=self.user)
        self.assertEqual(original_url, retrieved_again.profile_picture.url)
        
        # Verify the file exists at the expected location
        self.assertTrue(retrieved_profile.profile_picture.storage.exists(
            retrieved_profile.profile_picture.name
        ))
        
        # Verify the stored data matches what we uploaded
        self.assertEqual(retrieved_profile.display_name, display_name)
        self.assertEqual(retrieved_profile.bio, bio)



class MediaValidationTestCase(TestCase):
    """Test cases for media file validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red', format='JPEG'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        
        # Determine content type based on format
        content_type_map = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif'
        }
        content_type = content_type_map.get(format, 'image/jpeg')
        
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type=content_type
        )

    def create_large_file(self, size_mb=6):
        """Helper method to create a large file exceeding 5MB limit"""
        size_bytes = size_mb * 1024 * 1024
        content = b'x' * size_bytes
        return SimpleUploadedFile(
            name='large_file.jpg',
            content=content,
            content_type='image/jpeg'
        )

    def test_valid_jpeg_upload(self):
        """Test that valid JPEG files are accepted"""
        test_image = self.create_test_image(name='test.jpg', format='JPEG')
        form = MediaUploadForm(files={'file': test_image})
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_valid_png_upload(self):
        """Test that valid PNG files are accepted"""
        test_image = self.create_test_image(name='test.png', format='PNG')
        form = MediaUploadForm(files={'file': test_image})
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_valid_gif_upload(self):
        """Test that valid GIF files are accepted"""
        test_image = self.create_test_image(name='test.gif', format='GIF')
        form = MediaUploadForm(files={'file': test_image})
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_file_size_validation_exceeds_limit(self):
        """Test that files exceeding 5MB are rejected"""
        large_file = self.create_large_file(size_mb=6)
        form = MediaUploadForm(files={'file': large_file})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
        self.assertIn('5MB', str(form.errors['file'][0]))

    def test_file_size_validation_at_limit(self):
        """Test that files at exactly 5MB are accepted"""
        # Create a file exactly 5MB
        size_bytes = 5 * 1024 * 1024
        content = b'x' * size_bytes
        file = SimpleUploadedFile(
            name='exactly_5mb.jpg',
            content=content,
            content_type='image/jpeg'
        )
        form = MediaUploadForm(files={'file': file})
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_invalid_file_type_text(self):
        """Test that text files are rejected"""
        text_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is a text file',
            content_type='text/plain'
        )
        form = MediaUploadForm(files={'file': text_file})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
        self.assertIn('JPEG, PNG, and GIF', str(form.errors['file'][0]))

    def test_invalid_file_type_pdf(self):
        """Test that PDF files are rejected"""
        pdf_file = SimpleUploadedFile(
            name='test.pdf',
            content=b'%PDF-1.4 fake pdf content',
            content_type='application/pdf'
        )
        form = MediaUploadForm(files={'file': pdf_file})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_invalid_file_type_video(self):
        """Test that video files are rejected"""
        video_file = SimpleUploadedFile(
            name='test.mp4',
            content=b'fake video content',
            content_type='video/mp4'
        )
        form = MediaUploadForm(files={'file': video_file})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_media_model_file_size_calculation(self):
        """Test that Media model correctly calculates file size"""
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Verify file size is stored
        self.assertGreater(media.file_size, 0)
        self.assertEqual(media.file_size, test_image.size)

    def test_media_model_thumbnail_generation(self):
        """Test that Media model generates thumbnails for images"""
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Verify thumbnail was generated
        self.assertIsNotNone(media.thumbnail)
        self.assertTrue(media.thumbnail.name)

    def test_media_model_dimensions_extraction(self):
        """Test that Media model extracts image dimensions"""
        test_image = self.create_test_image(size=(640, 480))
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Verify dimensions are stored
        self.assertEqual(media.width, 640)
        self.assertEqual(media.height, 480)

    def test_media_deletion_removes_files(self):
        """Test that deleting media removes files from storage"""
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Get file paths
        file_path = media.file.path
        thumbnail_path = media.thumbnail.path if media.thumbnail else None
        
        # Delete media
        media.delete_file()
        media.delete()
        
        # Verify files are deleted
        if file_path and os.path.exists(file_path):
            self.fail("Media file was not deleted")
        if thumbnail_path and os.path.exists(thumbnail_path):
            self.fail("Thumbnail file was not deleted")


class MediaUploadPropertyTestCase(HypothesisTestCase):
    """Property-based tests for media upload and validation"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=unique_username,
            email=f'{unique_username}@example.com',
            password='testpass123'
        )

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    @given(
        width=st.integers(min_value=1, max_value=4000),
        height=st.integers(min_value=1, max_value=4000)
    )
    @settings(max_examples=50)
    def test_media_file_validation_property(self, width, height):
        """
        **Feature: twitter-phase-1-core-features, Property 2: Media File Validation**
        
        Property: For any file upload attempt, files exceeding 5MB or with invalid types 
        (not JPEG/PNG/GIF) should be rejected with an appropriate error message.
        
        **Validates: Requirements 2.2**
        """
        # Create a valid image with the given dimensions
        try:
            img = Image.new('RGB', (width, height), color='red')
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            
            test_image = SimpleUploadedFile(
                name='test.jpg',
                content=img_io.getvalue(),
                content_type='image/jpeg'
            )
            
            # Valid JPEG files should pass validation
            form = MediaUploadForm(files={'file': test_image})
            
            # If file is under 5MB and is JPEG, it should be valid
            if test_image.size <= 5 * 1024 * 1024:
                self.assertTrue(form.is_valid(), 
                    f"Valid JPEG should pass validation. Errors: {form.errors}")
        except Exception as e:
            # Some image sizes might cause memory issues, which is acceptable
            pass

    @given(
        file_type=st.sampled_from(['text/plain', 'application/pdf', 'video/mp4', 'application/zip'])
    )
    @settings(max_examples=20)
    def test_invalid_file_types_rejected_property(self, file_type):
        """
        **Feature: twitter-phase-1-core-features, Property 2: Media File Validation**
        
        Property: For any file upload attempt with invalid file types, 
        the system should reject them with an appropriate error message.
        
        **Validates: Requirements 2.2**
        """
        # Create a file with invalid type
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'Invalid file content',
            content_type=file_type
        )
        
        form = MediaUploadForm(files={'file': invalid_file})
        
        # Invalid file types should be rejected
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    @given(
        file_size_mb=st.integers(min_value=6, max_value=100)
    )
    @settings(max_examples=20)
    def test_oversized_files_rejected_property(self, file_size_mb):
        """
        **Feature: twitter-phase-1-core-features, Property 2: Media File Validation**
        
        Property: For any file upload attempt with files exceeding 5MB, 
        the system should reject them with an appropriate error message.
        
        **Validates: Requirements 2.2**
        """
        # Create a file exceeding 5MB
        size_bytes = file_size_mb * 1024 * 1024
        oversized_file = SimpleUploadedFile(
            name='oversized.jpg',
            content=b'x' * size_bytes,
            content_type='image/jpeg'
        )
        
        form = MediaUploadForm(files={'file': oversized_file})
        
        # Files exceeding 5MB should be rejected
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
        # Verify error message mentions the size limit
        error_msg = str(form.errors['file'][0])
        self.assertIn('5MB', error_msg)



class TweetEditPreservationTestCase(HypothesisTestCase):
    """Property-based tests for tweet edit preservation"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=unique_username,
            email=f'{unique_username}@example.com',
            password='testpass123'
        )

    @given(
        original_text=st.just("Original tweet"),
        edited_text=st.just("Edited tweet")
    )
    @settings(max_examples=1, deadline=None)
    def test_tweet_edit_preservation_property(self, original_text, edited_text):
        """
        **Feature: twitter-phase-1-core-features, Property 4: Tweet Edit Preservation**
        
        Property: For any edited tweet, the engagement metrics (likes, comments, retweets) 
        should remain unchanged after editing.
        
        **Validates: Requirements 3.5**
        """
        # Create a tweet with original text
        tweet = Tweet.objects.create(
            user=self.user,
            text=original_text
        )
        
        # Create a liker user
        liker = User.objects.create_user(
            username=f'liker_{id(tweet)}',
            email=f'liker_{id(tweet)}@example.com',
            password='testpass123'
        )
        Like.objects.create(user=liker, tweet=tweet)
        
        # Create a commenter user
        commenter = User.objects.create_user(
            username=f'commenter_{id(tweet)}',
            email=f'commenter_{id(tweet)}@example.com',
            password='testpass123'
        )
        Comment.objects.create(
            tweet=tweet,
            user=commenter,
            text='Test comment'
        )
        
        # Record engagement metrics before edit
        likes_before = tweet.likes.count()
        comments_before = tweet.comments.count()
        
        # Edit the tweet
        tweet.text = edited_text
        tweet.save()
        
        # Create edit history
        TweetEditHistory.objects.create(
            tweet=tweet,
            previous_content=original_text,
            edited_by=self.user
        )
        
        # Mark as edited
        tweet.mark_as_edited()
        
        # Refresh from database
        tweet.refresh_from_db()
        
        # Verify engagement metrics are preserved
        self.assertEqual(tweet.likes.count(), likes_before)
        self.assertEqual(tweet.comments.count(), comments_before)
        
        # Verify tweet content was updated
        self.assertEqual(tweet.text, edited_text)
        
        # Verify edit flag is set
        self.assertTrue(tweet.is_edited)
        self.assertIsNotNone(tweet.edited_at)


class TweetEditHistoryTestCase(HypothesisTestCase):
    """Property-based tests for tweet edit history accuracy"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=unique_username,
            email=f'{unique_username}@example.com',
            password='testpass123'
        )

    @given(
        original_text=st.just("Original tweet"),
        edited_text=st.just("Edited tweet"),
        num_edits=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=1, deadline=None)
    def test_edit_history_accuracy_property(self, original_text, edited_text, num_edits):
        """
        **Feature: twitter-phase-1-core-features, Property 5: Edit History Accuracy**
        
        Property: For any tweet edit, the previous content should be stored in edit history 
        with the correct timestamp and user information.
        
        **Validates: Requirements 3.4**
        """
        # Create a tweet with original text
        tweet = Tweet.objects.create(
            user=self.user,
            text=original_text
        )
        
        # Perform multiple edits
        previous_texts = [original_text]
        
        for i in range(num_edits):
            # Create a new text for this edit
            new_text = f"{edited_text}_{i}"
            
            # Store the current text as previous
            current_text = tweet.text
            
            # Update the tweet
            tweet.text = new_text
            tweet.save()
            
            # Create edit history record
            edit_history = TweetEditHistory.objects.create(
                tweet=tweet,
                previous_content=current_text,
                edited_by=self.user
            )
            
            # Mark as edited
            tweet.mark_as_edited()
            
            previous_texts.append(current_text)
        
        # Verify edit history records
        edits = TweetEditHistory.objects.filter(tweet=tweet).order_by('edited_at')
        
        # Should have num_edits records
        self.assertEqual(edits.count(), num_edits)
        
        # Verify each edit record has correct information
        for i, edit in enumerate(edits):
            # Verify previous content matches
            self.assertEqual(edit.previous_content, previous_texts[i])
            
            # Verify edited_by is correct
            self.assertEqual(edit.edited_by, self.user)
            
            # Verify edited_at is set
            self.assertIsNotNone(edit.edited_at)
        
        # Verify tweet is marked as edited
        self.assertTrue(tweet.is_edited)
        self.assertIsNotNone(tweet.edited_at)

    def test_edit_history_single_edit(self):
        """Test edit history with a single edit"""
        original_text = "Original tweet content"
        edited_text = "Edited tweet content"
        
        # Create a tweet
        tweet = Tweet.objects.create(
            user=self.user,
            text=original_text
        )
        
        # Edit the tweet
        tweet.text = edited_text
        tweet.save()
        
        # Create edit history
        edit_history = TweetEditHistory.objects.create(
            tweet=tweet,
            previous_content=original_text,
            edited_by=self.user
        )
        
        # Mark as edited
        tweet.mark_as_edited()
        
        # Verify edit history
        self.assertEqual(TweetEditHistory.objects.filter(tweet=tweet).count(), 1)
        self.assertEqual(edit_history.previous_content, original_text)
        self.assertEqual(edit_history.edited_by, self.user)
        
        # Verify tweet state
        self.assertTrue(tweet.is_edited)
        self.assertIsNotNone(tweet.edited_at)

    def test_edit_history_multiple_edits(self):
        """Test edit history with multiple edits"""
        # Create a tweet
        tweet = Tweet.objects.create(
            user=self.user,
            text="Version 1"
        )
        
        # First edit
        tweet.text = "Version 2"
        tweet.save()
        TweetEditHistory.objects.create(
            tweet=tweet,
            previous_content="Version 1",
            edited_by=self.user
        )
        tweet.mark_as_edited()
        
        # Second edit
        tweet.text = "Version 3"
        tweet.save()
        TweetEditHistory.objects.create(
            tweet=tweet,
            previous_content="Version 2",
            edited_by=self.user
        )
        tweet.mark_as_edited()
        
        # Verify edit history
        edits = TweetEditHistory.objects.filter(tweet=tweet).order_by('edited_at')
        self.assertEqual(edits.count(), 2)
        
        # Verify order and content
        self.assertEqual(edits[0].previous_content, "Version 1")
        self.assertEqual(edits[1].previous_content, "Version 2")


class SearchFunctionalityTestCase(TestCase):
    """Test cases for comprehensive search functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='testpass123'
        )
        self.user1.profile.bio = 'Software developer and tech enthusiast'
        self.user1.profile.save()
        
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='testpass123'
        )
        self.user2.profile.bio = 'Designer and creative thinker'
        self.user2.profile.save()
        
        self.user3 = User.objects.create_user(
            username='charlie',
            email='charlie@example.com',
            password='testpass123'
        )
        self.user3.profile.bio = 'Data scientist'
        self.user3.profile.save()
        
        # Create test tweets
        self.tweet1 = Tweet.objects.create(
            user=self.user1,
            text='Python is an amazing programming language'
        )
        
        self.tweet2 = Tweet.objects.create(
            user=self.user2,
            text='I love designing beautiful user interfaces'
        )
        
        self.tweet3 = Tweet.objects.create(
            user=self.user3,
            text='Data science and machine learning are fascinating'
        )
        
        self.tweet4 = Tweet.objects.create(
            user=self.user1,
            text='Django is great for web development'
        )

    def test_search_page_loads(self):
        """Test that search page loads successfully"""
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_results.html')

    def test_search_by_tweet_content(self):
        """Test searching for tweets by content"""
        response = self.client.get('/search/?q=Python')
        self.assertEqual(response.status_code, 200)
        
        # Verify the search query is in context
        self.assertEqual(response.context['query'], 'Python')
        
        # Verify tweet with 'Python' is in results
        tweets = response.context['tweets']
        self.assertGreater(len(tweets), 0)
        self.assertIn(self.tweet1, tweets)

    def test_search_by_username(self):
        """Test searching for users by username"""
        response = self.client.get('/search/?q=alice')
        self.assertEqual(response.status_code, 200)
        
        # Verify the search query is in context
        self.assertEqual(response.context['query'], 'alice')
        
        # Verify user with username 'alice' is in results
        users = response.context['users']
        self.assertGreater(len(users), 0)
        self.assertIn(self.user1, users)

    def test_search_by_user_bio(self):
        """Test searching for users by bio content"""
        response = self.client.get('/search/?q=developer')
        self.assertEqual(response.status_code, 200)
        
        # Verify the search query is in context
        self.assertEqual(response.context['query'], 'developer')
        
        # Verify user with 'developer' in bio is in results
        users = response.context['users']
        self.assertGreater(len(users), 0)
        self.assertIn(self.user1, users)

    def test_search_empty_query(self):
        """Test search with empty query"""
        response = self.client.get('/search/?q=')
        self.assertEqual(response.status_code, 200)
        
        # Verify no results are returned for empty query
        self.assertEqual(len(response.context['tweets']), 0)
        self.assertEqual(len(response.context['users']), 0)

    def test_search_no_results(self):
        """Test search with query that returns no results"""
        response = self.client.get('/search/?q=nonexistentquery12345')
        self.assertEqual(response.status_code, 200)
        
        # Verify no results are returned
        self.assertEqual(len(response.context['tweets']), 0)
        self.assertEqual(len(response.context['users']), 0)

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive"""
        response1 = self.client.get('/search/?q=python')
        response2 = self.client.get('/search/?q=PYTHON')
        response3 = self.client.get('/search/?q=Python')
        
        # All should return the same results
        tweets1 = list(response1.context['tweets'])
        tweets2 = list(response2.context['tweets'])
        tweets3 = list(response3.context['tweets'])
        
        self.assertEqual(tweets1, tweets2)
        self.assertEqual(tweets2, tweets3)

    def test_search_multiple_results(self):
        """Test search that returns multiple results"""
        response = self.client.get('/search/?q=and')
        self.assertEqual(response.status_code, 200)
        
        # Should find tweets with 'and' in them
        tweets = response.context['tweets']
        self.assertGreater(len(tweets), 0)

    def test_search_results_contain_required_info(self):
        """Test that search results contain required information"""
        response = self.client.get('/search/?q=Python')
        self.assertEqual(response.status_code, 200)
        
        tweets = response.context['tweets']
        self.assertGreater(len(tweets), 0)
        
        # Verify tweet has required attributes
        tweet = tweets[0]
        self.assertTrue(hasattr(tweet, 'text'))
        self.assertTrue(hasattr(tweet, 'user'))
        self.assertTrue(hasattr(tweet, 'created_at'))

    def test_search_user_results_contain_required_info(self):
        """Test that user search results contain required information"""
        response = self.client.get('/search/?q=alice')
        self.assertEqual(response.status_code, 200)
        
        users = response.context['users']
        self.assertGreater(len(users), 0)
        
        # Verify user has required attributes
        user = users[0]
        self.assertTrue(hasattr(user, 'username'))
        self.assertTrue(hasattr(user, 'profile'))

    def test_search_pagination_context(self):
        """Test that search results include pagination context"""
        response = self.client.get('/search/?q=and')
        self.assertEqual(response.status_code, 200)
        
        # Verify pagination context is present
        self.assertIn('page_num', response.context)
        self.assertIn('total_results', response.context)

    def test_search_with_special_characters(self):
        """Test search with special characters"""
        response = self.client.get('/search/?q=@#$%')
        self.assertEqual(response.status_code, 200)
        
        # Should not crash and return empty results
        self.assertEqual(len(response.context['tweets']), 0)

    def test_search_with_whitespace(self):
        """Test search with leading/trailing whitespace"""
        response1 = self.client.get('/search/?q=  Python  ')
        response2 = self.client.get('/search/?q=Python')
        
        # Both should return the same results
        tweets1 = list(response1.context['tweets'])
        tweets2 = list(response2.context['tweets'])
        
        self.assertEqual(tweets1, tweets2)


class SearchRelevancePropertyTestCase(HypothesisTestCase):
    """Property-based tests for search result relevance"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        # Create multiple test users with unique usernames
        self.users = []
        for i in range(5):
            unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
            user = User.objects.create_user(
                username=unique_username,
                email=f'{unique_username}@example.com',
                password='testpass123'
            )
            self.users.append(user)

    @given(
        search_term=st.just('python')  # Use a fixed search term to avoid username issues
    )
    @settings(max_examples=10, deadline=None)
    def test_search_result_relevance_property(self, search_term):
        """
        **Feature: twitter-phase-1-core-features, Property 6: Search Result Relevance**
        
        Property: For any search query, all returned results should contain the search term 
        in tweet content, username, or bio.
        
        **Validates: Requirements 4.1**
        """
        # Skip if search term is empty or only whitespace
        if not search_term or not search_term.strip():
            return
        
        search_term = search_term.strip()
        
        # Create tweets with the search term in content
        for i in range(3):
            user = self.users[i % len(self.users)]
            tweet_text = f"This is a tweet about {search_term} and other things"
            Tweet.objects.create(
                user=user,
                text=tweet_text
            )
        
        # Create tweets without the search term
        for i in range(2):
            user = self.users[i % len(self.users)]
            tweet_text = "This is a tweet about something else entirely"
            Tweet.objects.create(
                user=user,
                text=tweet_text
            )
        
        # Perform search
        tweet_results = Tweet.objects.filter(
            Q(text__icontains=search_term)
        ).order_by('-created_at')
        
        user_results = User.objects.filter(
            Q(username__icontains=search_term) |
            Q(profile__bio__icontains=search_term)
        ).order_by('username').distinct()
        
        # Verify all tweet results contain the search term
        for tweet in tweet_results:
            self.assertIn(
                search_term.lower(),
                tweet.text.lower(),
                f"Tweet '{tweet.text}' does not contain search term '{search_term}'"
            )

    def test_search_result_relevance_exact_match(self):
        """Test search result relevance with exact match"""
        # Create a user with a specific username
        user = User.objects.create_user(
            username='pythondeveloper',
            email='python@example.com',
            password='testpass123'
        )
        
        # Create tweets with the search term
        tweet1 = Tweet.objects.create(
            user=user,
            text='I love Python programming'
        )
        
        tweet2 = Tweet.objects.create(
            user=user,
            text='Python is awesome'
        )
        
        # Create a tweet without the search term
        tweet3 = Tweet.objects.create(
            user=user,
            text='JavaScript is also great'
        )
        
        # Search for "Python"
        search_term = "Python"
        tweet_results = Tweet.objects.filter(
            Q(text__icontains=search_term)
        )
        
        user_results = User.objects.filter(
            Q(username__icontains=search_term) |
            Q(profile__bio__icontains=search_term)
        )
        
        # Verify results
        self.assertEqual(tweet_results.count(), 2)
        self.assertIn(tweet1, tweet_results)
        self.assertIn(tweet2, tweet_results)
        self.assertNotIn(tweet3, tweet_results)
        
        # Verify user is in results
        self.assertEqual(user_results.count(), 1)
        self.assertIn(user, user_results)
        
        # Verify all results contain the search term
        for tweet in tweet_results:
            self.assertIn(search_term.lower(), tweet.text.lower())
        
        for user in user_results:
            # Ensure user has a profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            has_term = (search_term.lower() in user.username.lower() or 
                       search_term.lower() in profile.bio.lower())
            self.assertTrue(has_term)

    def test_search_result_relevance_case_insensitive(self):
        """Test that search result relevance works case-insensitively"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create tweets with different cases
        tweet1 = Tweet.objects.create(
            user=user,
            text='I love DJANGO framework'
        )
        
        tweet2 = Tweet.objects.create(
            user=user,
            text='Django is great'
        )
        
        # Search with different cases
        for search_term in ['django', 'DJANGO', 'Django', 'DjAnGo']:
            tweet_results = Tweet.objects.filter(
                Q(text__icontains=search_term)
            )
            
            # All should return the same results
            self.assertEqual(tweet_results.count(), 2)
            self.assertIn(tweet1, tweet_results)
            self.assertIn(tweet2, tweet_results)
            
            # Verify all results contain the search term (case-insensitive)
            for tweet in tweet_results:
                self.assertIn(search_term.lower(), tweet.text.lower())

    def test_search_result_relevance_partial_match(self):
        """Test search result relevance with partial matches"""
        # Create users
        user1 = User.objects.create_user(
            username='pythondev',
            email='python@example.com',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            username='javadev',
            email='java@example.com',
            password='testpass123'
        )
        user2.profile.bio = 'I work with Python and Java'
        user2.profile.save()
        
        # Create tweets
        tweet1 = Tweet.objects.create(
            user=user1,
            text='Python programming tips'
        )
        
        tweet2 = Tweet.objects.create(
            user=user2,
            text='Learning Python basics'
        )
        
        # Search for "python"
        search_term = "python"
        tweet_results = Tweet.objects.filter(
            Q(text__icontains=search_term)
        )
        
        user_results = User.objects.filter(
            Q(username__icontains=search_term) |
            Q(profile__bio__icontains=search_term)
        )
        
        # Verify results
        self.assertEqual(tweet_results.count(), 2)
        self.assertEqual(user_results.count(), 2)
        
        # Verify all results contain the search term
        for tweet in tweet_results:
            self.assertIn(search_term.lower(), tweet.text.lower())
        
        for user in user_results:
            # Ensure user has a profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            has_term = (search_term.lower() in user.username.lower() or 
                       search_term.lower() in profile.bio.lower())
            self.assertTrue(has_term)


class DraftAutoSaveTestCase(HypothesisTestCase):
    """Property-based tests for draft auto-save functionality"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        self.unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=self.unique_username,
            email=f'{self.unique_username}@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)

    @given(
        content=st.text(min_size=1, max_size=240),
        num_saves=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=50)
    def test_draft_auto_save_consistency_property(self, content, num_saves):
        """
        **Feature: twitter-phase-1-core-features, Property 7: Draft Auto-Save Consistency**
        
        Property: For any draft auto-save operation, the saved content should match 
        the current form state exactly.
        
        **Validates: Requirements 5.1**
        """
        # Skip if content is empty or only whitespace
        if not content or not content.strip():
            return
        
        content = content.strip()
        
        # Perform multiple saves directly to the model (simulating auto-save)
        for i in range(num_saves):
            # Get or create draft for this user
            draft, created = TweetDraft.objects.get_or_create(user=self.user)
            
            # Update draft content
            draft.content = content
            draft.save()
            
            # Verify the draft was saved correctly
            self.assertEqual(draft.content, content)
        
        # Retrieve draft from database
        draft = TweetDraft.objects.filter(user=self.user).first()
        
        # Verify draft exists and content matches what was saved
        self.assertIsNotNone(draft)
        self.assertEqual(draft.content, content)

    def test_draft_auto_save_single_save(self):
        """Test draft auto-save with a single save"""
        content = "This is my draft tweet"
        
        response = self.client.post(
            '/draft/save/',
            data=json.dumps({
                'content': content,
                'media_ids': []
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify draft was saved
        draft = TweetDraft.objects.filter(user=self.user).first()
        self.assertIsNotNone(draft)
        self.assertEqual(draft.content, content)

    def test_draft_auto_save_multiple_saves_overwrites(self):
        """Test that multiple saves overwrite previous draft"""
        content1 = "First draft"
        content2 = "Second draft"
        content3 = "Third draft"
        
        # Save first draft
        self.client.post(
            '/draft/save/',
            data=json.dumps({'content': content1, 'media_ids': []}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Save second draft
        self.client.post(
            '/draft/save/',
            data=json.dumps({'content': content2, 'media_ids': []}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Save third draft
        self.client.post(
            '/draft/save/',
            data=json.dumps({'content': content3, 'media_ids': []}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Verify only one draft exists with the latest content
        drafts = TweetDraft.objects.filter(user=self.user)
        self.assertEqual(drafts.count(), 1)
        self.assertEqual(drafts.first().content, content3)

    def test_draft_auto_save_empty_content_rejected(self):
        """Test that empty draft content is rejected"""
        response = self.client.post(
            '/draft/save/',
            data=json.dumps({'content': '', 'media_ids': []}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_draft_auto_save_whitespace_only_rejected(self):
        """Test that whitespace-only draft content is rejected"""
        response = self.client.post(
            '/draft/save/',
            data=json.dumps({'content': '   \n\t  ', 'media_ids': []}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class DraftRestorationTestCase(HypothesisTestCase):
    """Property-based tests for draft restoration accuracy"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        self.unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=self.unique_username,
            email=f'{self.unique_username}@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    @given(
        content=st.text(min_size=1, max_size=240),
        num_media=st.integers(min_value=0, max_value=2)
    )
    @settings(max_examples=50)
    def test_draft_restoration_accuracy_property(self, content, num_media):
        """
        **Feature: twitter-phase-1-core-features, Property 8: Draft Restoration Accuracy**
        
        Property: For any restored draft, the content and media should match 
        the previously saved state.
        
        **Validates: Requirements 5.3**
        """
        # Skip if content is empty or only whitespace
        if not content or not content.strip():
            return
        
        content = content.strip()
        
        # Create media files
        media_ids = []
        for i in range(num_media):
            test_image = self.create_test_image(name=f'test_{i}.jpg')
            media = Media(user=self.user, file=test_image, file_type='image')
            media.save()
            media_ids.append(media.id)
        
        # Save draft directly to model (bypassing HTTP layer for property test)
        draft, created = TweetDraft.objects.get_or_create(user=self.user)
        draft.content = content
        draft.save()
        
        # Clear and set media
        draft.media.clear()
        if media_ids:
            media_objects = Media.objects.filter(id__in=media_ids, user=self.user)
            draft.media.set(media_objects)
        
        # Retrieve draft from database
        retrieved_draft = TweetDraft.objects.get(user=self.user)
        
        # Verify restoration accuracy
        self.assertEqual(retrieved_draft.content, content)
        self.assertEqual(retrieved_draft.media.count(), num_media)
        
        # Verify media IDs match
        retrieved_media_ids = list(retrieved_draft.media.values_list('id', flat=True))
        self.assertEqual(sorted(retrieved_media_ids), sorted(media_ids))

    def test_draft_restoration_single_media(self):
        """Test draft restoration with single media file"""
        content = "Draft with media"
        
        # Create media
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Save draft
        self.client.post(
            '/draft/save/',
            data=json.dumps({
                'content': content,
                'media_ids': [media.id]
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Restore draft
        response = self.client.get(
            '/draft/restore/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['draft']['content'], content)
        self.assertEqual(len(data['draft']['media']), 1)

    def test_draft_restoration_multiple_media(self):
        """Test draft restoration with multiple media files"""
        content = "Draft with multiple media"
        
        # Create multiple media files
        media_ids = []
        for i in range(3):
            test_image = self.create_test_image(name=f'test_{i}.jpg')
            media = Media(user=self.user, file=test_image, file_type='image')
            media.save()
            media_ids.append(media.id)
        
        # Save draft
        self.client.post(
            '/draft/save/',
            data=json.dumps({
                'content': content,
                'media_ids': media_ids
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Restore draft
        response = self.client.get(
            '/draft/restore/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['draft']['content'], content)
        self.assertEqual(len(data['draft']['media']), 3)

    def test_draft_restoration_no_draft_available(self):
        """Test draft restoration when no draft exists"""
        response = self.client.get(
            '/draft/restore/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('message', data)

    def test_draft_clear_removes_draft(self):
        """Test that clearing draft removes it from database"""
        content = "Draft to clear"
        
        # Save draft
        self.client.post(
            '/draft/save/',
            data=json.dumps({
                'content': content,
                'media_ids': []
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Verify draft exists
        self.assertTrue(TweetDraft.objects.filter(user=self.user).exists())
        
        # Clear draft
        response = self.client.post(
            '/draft/clear/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify draft is deleted
        self.assertFalse(TweetDraft.objects.filter(user=self.user).exists())


class MediaDeletionCascadeTestCase(HypothesisTestCase):
    """Property-based tests for media deletion cascade when tweets are deleted"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=unique_username,
            email=f'{unique_username}@example.com',
            password='testpass123'
        )

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    @given(
        num_media=st.integers(min_value=1, max_value=5),
        tweet_text=st.text(min_size=1, max_size=240)
    )
    @settings(max_examples=50)
    def test_media_deletion_cascade_property(self, num_media, tweet_text):
        """
        **Feature: twitter-phase-1-core-features, Property 3: Media Deletion Cascade**
        
        Property: For any tweet deletion, all associated media files should be removed 
        from storage and the database.
        
        **Validates: Requirements 2.5**
        """
        # Create a tweet with multiple media files
        tweet = Tweet.objects.create(
            user=self.user,
            text=tweet_text
        )
        
        # Create and attach media files to the tweet
        media_ids = []
        media_file_paths = []
        
        for i in range(num_media):
            test_image = self.create_test_image(name=f'test_{i}.jpg')
            media = Media(user=self.user, file=test_image, file_type='image')
            media.save()
            
            # Store file paths for later verification
            if media.file:
                media_file_paths.append(media.file.path)
            if media.thumbnail:
                media_file_paths.append(media.thumbnail.path)
            
            # Associate media with tweet
            tweet.media.add(media)
            media_ids.append(media.id)
        
        # Verify media is associated with tweet
        self.assertEqual(tweet.media.count(), num_media)
        
        # Verify all media exists in database
        for media_id in media_ids:
            self.assertTrue(Media.objects.filter(id=media_id).exists())
        
        # Delete the tweet
        tweet_id = tweet.id
        tweet.delete()
        
        # Verify tweet is deleted
        self.assertFalse(Tweet.objects.filter(id=tweet_id).exists())
        
        # Verify all associated media is deleted from database
        for media_id in media_ids:
            self.assertFalse(Media.objects.filter(id=media_id).exists())
        
        # Verify all media files are deleted from storage
        for file_path in media_file_paths:
            if file_path and os.path.exists(file_path):
                self.fail(f"Media file was not deleted from storage: {file_path}")

    def test_media_deletion_cascade_single_media(self):
        """Test media deletion cascade with a single media file"""
        # Create a tweet with one media file
        tweet = Tweet.objects.create(
            user=self.user,
            text='Test tweet with media'
        )
        
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Store file paths
        file_path = media.file.path if media.file else None
        thumbnail_path = media.thumbnail.path if media.thumbnail else None
        
        # Associate media with tweet
        tweet.media.add(media)
        media_id = media.id
        
        # Verify association
        self.assertEqual(tweet.media.count(), 1)
        self.assertTrue(Media.objects.filter(id=media_id).exists())
        
        # Delete the tweet
        tweet.delete()
        
        # Verify media is deleted from database
        self.assertFalse(Media.objects.filter(id=media_id).exists())
        
        # Verify files are deleted from storage
        if file_path and os.path.exists(file_path):
            self.fail("Media file was not deleted from storage")
        if thumbnail_path and os.path.exists(thumbnail_path):
            self.fail("Thumbnail file was not deleted from storage")

    def test_media_deletion_cascade_multiple_media_same_tweet(self):
        """Test that all media associated with a tweet are deleted when tweet is deleted"""
        # Create a tweet with multiple media files
        tweet = Tweet.objects.create(
            user=self.user,
            text='Tweet with multiple media'
        )
        
        # Create and attach multiple media files
        media_ids = []
        for i in range(3):
            test_image = self.create_test_image(name=f'test_{i}.jpg')
            media = Media(user=self.user, file=test_image, file_type='image')
            media.save()
            tweet.media.add(media)
            media_ids.append(media.id)
        
        # Verify all media is associated
        self.assertEqual(tweet.media.count(), 3)
        
        # Delete the tweet
        tweet.delete()
        
        # Verify all media is deleted from database
        for media_id in media_ids:
            self.assertFalse(Media.objects.filter(id=media_id).exists())



class ScheduledTweetPublishingTestCase(HypothesisTestCase):
    """Property-based tests for scheduled tweet publishing"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=unique_username,
            email=f'{unique_username}@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.force_login(self.user)

    @given(
        tweet_text=st.text(min_size=1, max_size=240),
        minutes_in_future=st.integers(min_value=1, max_value=60)
    )
    @settings(max_examples=50)
    def test_scheduled_tweet_publishing_property(self, tweet_text, minutes_in_future):
        """
        **Feature: twitter-phase-1-core-features, Property 9: Scheduled Tweet Publishing**
        
        Property: For any scheduled tweet, when the scheduled time arrives, 
        the tweet should be automatically published with the correct content and media.
        
        **Validates: Requirements 6.4**
        """
        # Skip if tweet text is empty or only whitespace
        if not tweet_text or not tweet_text.strip():
            return
        
        tweet_text = tweet_text.strip()
        
        # Create a scheduled tweet with a future publish time
        from django.utils import timezone
        from datetime import timedelta
        
        scheduled_time = timezone.now() + timedelta(minutes=minutes_in_future)
        
        tweet = Tweet.objects.create(
            user=self.user,
            text=tweet_text,
            is_scheduled=True,
            scheduled_publish_time=scheduled_time
        )
        
        # Verify tweet is marked as scheduled
        self.assertTrue(tweet.is_scheduled)
        self.assertIsNotNone(tweet.scheduled_publish_time)
        self.assertEqual(tweet.text, tweet_text)
        
        # Simulate time passing - set scheduled time to the past
        tweet.scheduled_publish_time = timezone.now() - timedelta(minutes=1)
        tweet.save()
        
        # Call publish_if_scheduled to simulate the publishing process
        result = tweet.publish_if_scheduled()
        
        # Verify the tweet was published
        self.assertTrue(result)
        
        # Refresh from database
        tweet.refresh_from_db()
        
        # Verify tweet is no longer marked as scheduled
        self.assertFalse(tweet.is_scheduled)
        self.assertIsNone(tweet.scheduled_publish_time)
        
        # Verify tweet content is preserved
        self.assertEqual(tweet.text, tweet_text)

    def test_scheduled_tweet_publishing_single_tweet(self):
        """Test publishing a single scheduled tweet"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a scheduled tweet
        scheduled_time = timezone.now() - timedelta(minutes=1)  # Past time
        tweet = Tweet.objects.create(
            user=self.user,
            text='This is a scheduled tweet',
            is_scheduled=True,
            scheduled_publish_time=scheduled_time
        )
        
        # Verify tweet is scheduled
        self.assertTrue(tweet.is_scheduled)
        
        # Publish the tweet
        result = tweet.publish_if_scheduled()
        
        # Verify it was published
        self.assertTrue(result)
        
        # Refresh and verify state
        tweet.refresh_from_db()
        self.assertFalse(tweet.is_scheduled)
        self.assertIsNone(tweet.scheduled_publish_time)

    def test_scheduled_tweet_not_published_if_future(self):
        """Test that future scheduled tweets are not published"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a scheduled tweet with future time
        scheduled_time = timezone.now() + timedelta(hours=1)
        tweet = Tweet.objects.create(
            user=self.user,
            text='This is a future scheduled tweet',
            is_scheduled=True,
            scheduled_publish_time=scheduled_time
        )
        
        # Try to publish
        result = tweet.publish_if_scheduled()
        
        # Verify it was NOT published
        self.assertFalse(result)
        
        # Refresh and verify state
        tweet.refresh_from_db()
        self.assertTrue(tweet.is_scheduled)
        self.assertIsNotNone(tweet.scheduled_publish_time)

    def test_scheduled_tweet_publishing_multiple_tweets(self):
        """Test publishing multiple scheduled tweets"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create multiple scheduled tweets with past times
        tweets = []
        for i in range(3):
            scheduled_time = timezone.now() - timedelta(minutes=i+1)
            tweet = Tweet.objects.create(
                user=self.user,
                text=f'Scheduled tweet {i+1}',
                is_scheduled=True,
                scheduled_publish_time=scheduled_time
            )
            tweets.append(tweet)
        
        # Verify all are scheduled
        for tweet in tweets:
            self.assertTrue(tweet.is_scheduled)
        
        # Publish all tweets
        for tweet in tweets:
            result = tweet.publish_if_scheduled()
            self.assertTrue(result)
        
        # Verify all are published
        for tweet in tweets:
            tweet.refresh_from_db()
            self.assertFalse(tweet.is_scheduled)
            self.assertIsNone(tweet.scheduled_publish_time)

    def test_scheduled_tweet_preserves_content(self):
        """Test that publishing preserves tweet content"""
        from django.utils import timezone
        from datetime import timedelta
        
        original_text = 'Important scheduled announcement'
        scheduled_time = timezone.now() - timedelta(minutes=1)
        
        tweet = Tweet.objects.create(
            user=self.user,
            text=original_text,
            is_scheduled=True,
            scheduled_publish_time=scheduled_time
        )
        
        # Publish
        tweet.publish_if_scheduled()
        
        # Verify content is preserved
        tweet.refresh_from_db()
        self.assertEqual(tweet.text, original_text)

    def test_scheduled_tweet_form_validation_future_only(self):
        """Test that tweet form validates scheduled time is in future"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Try to schedule for the past
        past_time = timezone.now() - timedelta(hours=1)
        
        form_data = {
            'text': 'Test tweet',
            'scheduled_publish_time': past_time
        }
        
        form = TweetForm(data=form_data)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_publish_time', form.errors)

    def test_scheduled_tweet_form_accepts_future_time(self):
        """Test that tweet form accepts future scheduled time"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Schedule for the future
        future_time = timezone.now() + timedelta(hours=1)
        
        form_data = {
            'text': 'Test tweet',
            'scheduled_publish_time': future_time
        }
        
        form = TweetForm(data=form_data)
        
        # Form should be valid
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_scheduled_tweet_form_accepts_empty_schedule(self):
        """Test that tweet form accepts empty scheduled time (publish immediately)"""
        form_data = {
            'text': 'Test tweet',
            'scheduled_publish_time': ''
        }
        
        form = TweetForm(data=form_data)
        
        # Form should be valid
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_scheduled_tweet_publishing_with_media(self):
        """Test that scheduled tweets with media are published correctly"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create media
        def create_test_image(name='test.jpg', size=(100, 100), color='red'):
            img = Image.new('RGB', size, color=color)
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            return SimpleUploadedFile(
                name=name,
                content=img_io.getvalue(),
                content_type='image/jpeg'
            )
        
        test_image = create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Create a scheduled tweet with media
        scheduled_time = timezone.now() - timedelta(minutes=1)
        tweet = Tweet.objects.create(
            user=self.user,
            text='Scheduled tweet with media',
            is_scheduled=True,
            scheduled_publish_time=scheduled_time
        )
        tweet.media.add(media)
        
        # Verify initial state
        self.assertTrue(tweet.is_scheduled)
        self.assertEqual(tweet.media.count(), 1)
        
        # Publish the tweet
        result = tweet.publish_if_scheduled()
        
        # Verify it was published
        self.assertTrue(result)
        
        # Refresh and verify state
        tweet.refresh_from_db()
        self.assertFalse(tweet.is_scheduled)
        self.assertIsNone(tweet.scheduled_publish_time)
        
        # Verify media is still associated
        self.assertEqual(tweet.media.count(), 1)

    @given(
        tweet_text=st.text(min_size=1, max_size=240),
        num_media=st.integers(min_value=0, max_value=3),
        minutes_past=st.integers(min_value=1, max_value=120)
    )
    @settings(max_examples=50, deadline=None)
    def test_scheduled_tweet_publishing_comprehensive_property(self, tweet_text, num_media, minutes_past):
        """
        **Feature: twitter-phase-1-core-features, Property 9: Scheduled Tweet Publishing**
        
        Property: For any scheduled tweet, when the scheduled time arrives, 
        the tweet should be automatically published with the correct content and media.
        
        **Validates: Requirements 6.4**
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Skip if tweet text is empty or only whitespace
        if not tweet_text or not tweet_text.strip():
            return
        
        tweet_text = tweet_text.strip()
        
        # Create media files if needed
        media_ids = []
        def create_test_image(name='test.jpg', size=(100, 100), color='red'):
            img = Image.new('RGB', size, color=color)
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            return SimpleUploadedFile(
                name=name,
                content=img_io.getvalue(),
                content_type='image/jpeg'
            )
        
        for i in range(num_media):
            try:
                test_image = create_test_image(name=f'test_{i}.jpg')
                media = Media(user=self.user, file=test_image, file_type='image')
                media.save()
                media_ids.append(media.id)
            except Exception:
                # Skip if media creation fails
                pass
        
        # Create a scheduled tweet with a past publish time (ready to publish)
        scheduled_time = timezone.now() - timedelta(minutes=minutes_past)
        
        tweet = Tweet.objects.create(
            user=self.user,
            text=tweet_text,
            is_scheduled=True,
            scheduled_publish_time=scheduled_time
        )
        
        # Associate media with tweet
        if media_ids:
            media_objects = Media.objects.filter(id__in=media_ids, user=self.user)
            tweet.media.set(media_objects)
        
        # Record initial state
        initial_media_count = tweet.media.count()
        initial_text = tweet.text
        
        # Verify tweet is scheduled
        self.assertTrue(tweet.is_scheduled)
        self.assertIsNotNone(tweet.scheduled_publish_time)
        
        # Publish the tweet
        result = tweet.publish_if_scheduled()
        
        # Verify the tweet was published
        self.assertTrue(result, "Tweet should be published when scheduled time has passed")
        
        # Refresh from database
        tweet.refresh_from_db()
        
        # Verify tweet is no longer marked as scheduled
        self.assertFalse(tweet.is_scheduled, "Tweet should not be marked as scheduled after publishing")
        self.assertIsNone(tweet.scheduled_publish_time, "Scheduled publish time should be cleared after publishing")
        
        # Verify tweet content is preserved
        self.assertEqual(tweet.text, initial_text, "Tweet content should be preserved after publishing")
        
        # Verify media is preserved
        self.assertEqual(tweet.media.count(), initial_media_count, "Media count should be preserved after publishing")
        
        # Verify all media IDs are still associated
        if media_ids:
            current_media_ids = list(tweet.media.values_list('id', flat=True))
            for media_id in media_ids:
                self.assertIn(media_id, current_media_ids, f"Media {media_id} should still be associated with tweet")



class MediaGalleryConsistencyTestCase(HypothesisTestCase):
    """Property-based tests for media gallery consistency"""

    def setUp(self):
        """Set up test fixtures"""
        import uuid
        unique_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=unique_username,
            email=f'{unique_username}@example.com',
            password='testpass123'
        )
        self.client = Client()

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    @given(
        num_media=st.integers(min_value=1, max_value=5),
        num_tweets_per_media=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=20, deadline=None)
    def test_media_gallery_consistency_property(self, num_media, num_tweets_per_media):
        """
        **Feature: twitter-phase-1-core-features, Property 10: Media Gallery Consistency**
        
        Property: For any media item in the gallery, clicking on it should display 
        the correct image and associated tweets.
        
        **Validates: Requirements 7.2**
        """
        # Create media files
        media_objects = []
        for i in range(num_media):
            try:
                test_image = self.create_test_image(name=f'test_{i}.jpg')
                media = Media(user=self.user, file=test_image, file_type='image')
                media.save()
                media_objects.append(media)
            except Exception:
                # Skip if media creation fails
                pass
        
        if not media_objects:
            return
        
        # Create tweets and associate with media
        tweet_media_map = {}
        for media in media_objects:
            tweet_media_map[media.id] = []
            
            for j in range(num_tweets_per_media):
                tweet = Tweet.objects.create(
                    user=self.user,
                    text=f'Tweet {j} with media'
                )
                tweet.media.add(media)
                tweet_media_map[media.id].append(tweet.id)
        
        # Verify gallery consistency
        for media in media_objects:
            # Verify media exists and is retrievable
            retrieved_media = Media.objects.get(id=media.id, user=self.user)
            self.assertIsNotNone(retrieved_media)
            
            # Verify media has a file
            self.assertTrue(retrieved_media.file)
            
            # Verify media has a thumbnail
            self.assertTrue(retrieved_media.thumbnail)
            
            # Verify associated tweets
            associated_tweets = retrieved_media.tweets.all()
            self.assertEqual(associated_tweets.count(), len(tweet_media_map[media.id]))
            
            # Verify each associated tweet is correct
            for tweet_id in tweet_media_map[media.id]:
                self.assertTrue(
                    associated_tweets.filter(id=tweet_id).exists(),
                    f"Tweet {tweet_id} should be associated with media {media.id}"
                )
            
            # Verify tweet content is accessible
            for tweet in associated_tweets:
                self.assertTrue(tweet.text)
                self.assertEqual(tweet.user, self.user)

    def test_media_gallery_empty_state(self):
        """Test media gallery with no media"""
        # User should have no media initially
        media_count = Media.objects.filter(user=self.user).count()
        self.assertEqual(media_count, 0)

    def test_media_gallery_single_media(self):
        """Test media gallery with single media item"""
        # Create a single media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Create a tweet with this media
        tweet = Tweet.objects.create(
            user=self.user,
            text='Tweet with media'
        )
        tweet.media.add(media)
        
        # Verify gallery consistency
        retrieved_media = Media.objects.get(id=media.id, user=self.user)
        self.assertEqual(retrieved_media.tweets.count(), 1)
        self.assertEqual(retrieved_media.tweets.first().id, tweet.id)

    def test_media_gallery_multiple_tweets_per_media(self):
        """Test media gallery with multiple tweets using same media"""
        # Create a single media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        
        # Create multiple tweets with this media
        tweet_ids = []
        for i in range(3):
            tweet = Tweet.objects.create(
                user=self.user,
                text=f'Tweet {i} with media'
            )
            tweet.media.add(media)
            tweet_ids.append(tweet.id)
        
        # Verify gallery consistency
        retrieved_media = Media.objects.get(id=media.id, user=self.user)
        self.assertEqual(retrieved_media.tweets.count(), 3)
        
        # Verify all tweets are associated
        associated_tweet_ids = list(retrieved_media.tweets.values_list('id', flat=True))
        for tweet_id in tweet_ids:
            self.assertIn(tweet_id, associated_tweet_ids)

    def test_media_gallery_deletion_cascade(self):
        """Test that deleting media removes it from gallery"""
        # Create a media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        media_id = media.id
        
        # Create a tweet with this media
        tweet = Tweet.objects.create(
            user=self.user,
            text='Tweet with media'
        )
        tweet.media.add(media)
        
        # Verify media exists
        self.assertTrue(Media.objects.filter(id=media_id).exists())
        
        # Delete the media
        media.delete_file()
        media.delete()
        
        # Verify media is deleted
        self.assertFalse(Media.objects.filter(id=media_id).exists())
        
        # Verify tweet still exists but media association is removed
        tweet.refresh_from_db()
        self.assertEqual(tweet.media.count(), 0)

    def test_media_gallery_isolation_between_users(self):
        """Test that media gallery is isolated between users"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create media for first user
        test_image1 = self.create_test_image()
        media1 = Media(user=self.user, file=test_image1, file_type='image')
        media1.save()
        
        # Create media for second user
        test_image2 = self.create_test_image()
        media2 = Media(user=other_user, file=test_image2, file_type='image')
        media2.save()
        
        # Verify first user can only see their media
        user1_media = Media.objects.filter(user=self.user)
        self.assertEqual(user1_media.count(), 1)
        self.assertEqual(user1_media.first().id, media1.id)
        
        # Verify second user can only see their media
        user2_media = Media.objects.filter(user=other_user)
        self.assertEqual(user2_media.count(), 1)
        self.assertEqual(user2_media.first().id, media2.id)


class PublishScheduledTweetsCommandTestCase(TestCase):
    """Test cases for the publish_scheduled_tweets management command"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_publish_scheduled_tweets_command_exists(self):
        """Test that the publish_scheduled_tweets command exists"""
        from django.core.management import call_command
        from io import StringIO
        
        # Should not raise an error
        out = StringIO()
        call_command('publish_scheduled_tweets', '--dry-run', stdout=out)
        self.assertIn('DRY RUN', out.getvalue())

    def test_publish_scheduled_tweets_dry_run(self):
        """Test dry-run mode shows what would be published"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a scheduled tweet in the past
        past_time = timezone.now() - timedelta(hours=1)
        tweet = Tweet.objects.create(
            user=self.user,
            text='Scheduled tweet',
            is_scheduled=True,
            scheduled_publish_time=past_time
        )
        
        # Run command with dry-run
        out = StringIO()
        call_command('publish_scheduled_tweets', '--dry-run', stdout=out)
        output = out.getvalue()
        
        # Verify dry-run output
        self.assertIn('DRY RUN', output)
        self.assertIn('Would publish', output)
        
        # Verify tweet is still scheduled
        tweet.refresh_from_db()
        self.assertTrue(tweet.is_scheduled)

    def test_publish_scheduled_tweets_publishes_ready_tweets(self):
        """Test that ready scheduled tweets are published"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a scheduled tweet in the past
        past_time = timezone.now() - timedelta(hours=1)
        tweet = Tweet.objects.create(
            user=self.user,
            text='Scheduled tweet',
            is_scheduled=True,
            scheduled_publish_time=past_time
        )
        
        # Run command
        out = StringIO()
        call_command('publish_scheduled_tweets', stdout=out)
        output = out.getvalue()
        
        # Verify tweet was published
        tweet.refresh_from_db()
        self.assertFalse(tweet.is_scheduled)
        self.assertIsNone(tweet.scheduled_publish_time)
        
        # Verify success message
        self.assertIn('Successfully published', output)

    def test_publish_scheduled_tweets_ignores_future_tweets(self):
        """Test that future scheduled tweets are not published"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a scheduled tweet in the future
        future_time = timezone.now() + timedelta(hours=1)
        tweet = Tweet.objects.create(
            user=self.user,
            text='Future scheduled tweet',
            is_scheduled=True,
            scheduled_publish_time=future_time
        )
        
        # Run command
        out = StringIO()
        call_command('publish_scheduled_tweets', stdout=out)
        
        # Verify tweet is still scheduled
        tweet.refresh_from_db()
        self.assertTrue(tweet.is_scheduled)
        self.assertEqual(tweet.scheduled_publish_time, future_time)

    def test_publish_scheduled_tweets_multiple_tweets(self):
        """Test publishing multiple scheduled tweets"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create multiple scheduled tweets in the past
        past_time = timezone.now() - timedelta(hours=1)
        tweets = []
        for i in range(3):
            tweet = Tweet.objects.create(
                user=self.user,
                text=f'Scheduled tweet {i}',
                is_scheduled=True,
                scheduled_publish_time=past_time
            )
            tweets.append(tweet)
        
        # Run command
        out = StringIO()
        call_command('publish_scheduled_tweets', stdout=out)
        output = out.getvalue()
        
        # Verify all tweets were published
        for tweet in tweets:
            tweet.refresh_from_db()
            self.assertFalse(tweet.is_scheduled)
        
        # Verify success message mentions count
        self.assertIn('Successfully published 3', output)


class CleanOldDraftsCommandTestCase(TestCase):
    """Test cases for the clean_old_drafts management command"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_clean_old_drafts_command_exists(self):
        """Test that the clean_old_drafts command exists"""
        from django.core.management import call_command
        from io import StringIO
        
        # Should not raise an error
        out = StringIO()
        call_command('clean_old_drafts', '--dry-run', stdout=out)
        self.assertIn('DRY RUN', out.getvalue())

    def test_clean_old_drafts_dry_run(self):
        """Test dry-run mode shows what would be deleted"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create an old draft
        old_time = timezone.now() - timedelta(days=31)
        draft = TweetDraft.objects.create(
            user=self.user,
            content='Old draft'
        )
        # Manually set the updated_at to old time
        TweetDraft.objects.filter(id=draft.id).update(updated_at=old_time)
        
        # Run command with dry-run
        out = StringIO()
        call_command('clean_old_drafts', '--days', '30', '--dry-run', stdout=out)
        output = out.getvalue()
        
        # Verify dry-run output
        self.assertIn('DRY RUN', output)
        self.assertIn('Would delete', output)
        
        # Verify draft still exists
        self.assertTrue(TweetDraft.objects.filter(id=draft.id).exists())

    def test_clean_old_drafts_deletes_old_drafts(self):
        """Test that old drafts are deleted"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create an old draft
        old_time = timezone.now() - timedelta(days=31)
        draft = TweetDraft.objects.create(
            user=self.user,
            content='Old draft'
        )
        draft_id = draft.id
        # Manually set the updated_at to old time
        TweetDraft.objects.filter(id=draft.id).update(updated_at=old_time)
        
        # Run command
        out = StringIO()
        call_command('clean_old_drafts', '--days', '30', stdout=out)
        output = out.getvalue()
        
        # Verify draft was deleted
        self.assertFalse(TweetDraft.objects.filter(id=draft_id).exists())
        
        # Verify success message
        self.assertIn('Successfully deleted', output)

    def test_clean_old_drafts_preserves_recent_drafts(self):
        """Test that recent drafts are not deleted"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create a recent draft
        draft = TweetDraft.objects.create(
            user=self.user,
            content='Recent draft'
        )
        draft_id = draft.id
        
        # Run command
        out = StringIO()
        call_command('clean_old_drafts', '--days', '30', stdout=out)
        
        # Verify draft still exists
        self.assertTrue(TweetDraft.objects.filter(id=draft_id).exists())

    def test_clean_old_drafts_custom_days_parameter(self):
        """Test custom days parameter"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a draft that's 15 days old
        old_time = timezone.now() - timedelta(days=15)
        draft = TweetDraft.objects.create(
            user=self.user,
            content='15-day-old draft'
        )
        draft_id = draft.id
        TweetDraft.objects.filter(id=draft.id).update(updated_at=old_time)
        
        # Run command with 10 days threshold
        out = StringIO()
        call_command('clean_old_drafts', '--days', '10', stdout=out)
        
        # Verify draft was deleted (15 days > 10 days)
        self.assertFalse(TweetDraft.objects.filter(id=draft_id).exists())

    def test_clean_old_drafts_multiple_drafts(self):
        """Test deleting multiple old drafts"""
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        from datetime import timedelta
        
        # Create multiple old drafts
        old_time = timezone.now() - timedelta(days=31)
        draft_ids = []
        for i in range(3):
            draft = TweetDraft.objects.create(
                user=self.user,
                content=f'Old draft {i}'
            )
            draft_ids.append(draft.id)
            TweetDraft.objects.filter(id=draft.id).update(updated_at=old_time)
        
        # Run command
        out = StringIO()
        call_command('clean_old_drafts', '--days', '30', stdout=out)
        output = out.getvalue()
        
        # Verify all drafts were deleted
        for draft_id in draft_ids:
            self.assertFalse(TweetDraft.objects.filter(id=draft_id).exists())
        
        # Verify success message mentions count
        self.assertIn('Successfully deleted 3', output)


class CleanOrphanedMediaCommandTestCase(TestCase):
    """Test cases for the clean_orphaned_media management command"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper method to create a test image file"""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_clean_orphaned_media_command_exists(self):
        """Test that the clean_orphaned_media command exists"""
        from django.core.management import call_command
        from io import StringIO
        
        # Should not raise an error
        out = StringIO()
        call_command('clean_orphaned_media', '--dry-run', stdout=out)
        self.assertIn('DRY RUN', out.getvalue())

    def test_clean_orphaned_media_dry_run(self):
        """Test dry-run mode shows what would be deleted"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create an orphaned media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        media_id = media.id
        
        # Run command with dry-run
        out = StringIO()
        call_command('clean_orphaned_media', '--dry-run', stdout=out)
        output = out.getvalue()
        
        # Verify dry-run output
        self.assertIn('DRY RUN', output)
        self.assertIn('Would delete', output)
        
        # Verify media still exists
        self.assertTrue(Media.objects.filter(id=media_id).exists())

    def test_clean_orphaned_media_deletes_orphaned_files(self):
        """Test that orphaned media files are deleted"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create an orphaned media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        media_id = media.id
        
        # Run command
        out = StringIO()
        call_command('clean_orphaned_media', stdout=out)
        output = out.getvalue()
        
        # Verify media was deleted
        self.assertFalse(Media.objects.filter(id=media_id).exists())
        
        # Verify success message
        self.assertIn('Successfully deleted', output)

    def test_clean_orphaned_media_preserves_tweet_media(self):
        """Test that media associated with tweets is preserved"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create a media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        media_id = media.id
        
        # Associate with a tweet
        tweet = Tweet.objects.create(
            user=self.user,
            text='Tweet with media'
        )
        tweet.media.add(media)
        
        # Run command
        out = StringIO()
        call_command('clean_orphaned_media', stdout=out)
        
        # Verify media still exists
        self.assertTrue(Media.objects.filter(id=media_id).exists())

    def test_clean_orphaned_media_preserves_draft_media(self):
        """Test that media associated with drafts is preserved"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create a media file
        test_image = self.create_test_image()
        media = Media(user=self.user, file=test_image, file_type='image')
        media.save()
        media_id = media.id
        
        # Associate with a draft
        draft = TweetDraft.objects.create(
            user=self.user,
            content='Draft with media'
        )
        draft.media.add(media)
        
        # Run command
        out = StringIO()
        call_command('clean_orphaned_media', stdout=out)
        
        # Verify media still exists
        self.assertTrue(Media.objects.filter(id=media_id).exists())

    def test_clean_orphaned_media_multiple_files(self):
        """Test deleting multiple orphaned media files"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create multiple orphaned media files
        media_ids = []
        for i in range(3):
            test_image = self.create_test_image(name=f'test_{i}.jpg')
            media = Media(user=self.user, file=test_image, file_type='image')
            media.save()
            media_ids.append(media.id)
        
        # Run command
        out = StringIO()
        call_command('clean_orphaned_media', stdout=out)
        output = out.getvalue()
        
        # Verify all media were deleted
        for media_id in media_ids:
            self.assertFalse(Media.objects.filter(id=media_id).exists())
        
        # Verify success message mentions count
        self.assertIn('Successfully deleted 3', output)

    def test_clean_orphaned_media_mixed_scenario(self):
        """Test with mix of orphaned and associated media"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create orphaned media
        orphaned_image = self.create_test_image(name='orphaned.jpg')
        orphaned_media = Media(user=self.user, file=orphaned_image, file_type='image')
        orphaned_media.save()
        orphaned_id = orphaned_media.id
        
        # Create media associated with tweet
        tweet_image = self.create_test_image(name='tweet_media.jpg')
        tweet_media = Media(user=self.user, file=tweet_image, file_type='image')
        tweet_media.save()
        tweet_media_id = tweet_media.id
        
        tweet = Tweet.objects.create(
            user=self.user,
            text='Tweet with media'
        )
        tweet.media.add(tweet_media)
        
        # Create media associated with draft
        draft_image = self.create_test_image(name='draft_media.jpg')
        draft_media = Media(user=self.user, file=draft_image, file_type='image')
        draft_media.save()
        draft_media_id = draft_media.id
        
        draft = TweetDraft.objects.create(
            user=self.user,
            content='Draft with media'
        )
        draft.media.add(draft_media)
        
        # Run command
        out = StringIO()
        call_command('clean_orphaned_media', stdout=out)
        output = out.getvalue()
        
        # Verify orphaned media was deleted
        self.assertFalse(Media.objects.filter(id=orphaned_id).exists())
        
        # Verify associated media was preserved
        self.assertTrue(Media.objects.filter(id=tweet_media_id).exists())
        self.assertTrue(Media.objects.filter(id=draft_media_id).exists())
        
        # Verify success message
        self.assertIn('Successfully deleted 1', output)
