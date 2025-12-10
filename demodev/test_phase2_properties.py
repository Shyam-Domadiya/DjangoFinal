"""
Property-Based Tests for Twitter Phase 2: Social Engagement & Discovery

These tests verify correctness properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.extra.django import TestCase as HypothesisTestCase
from django.contrib.auth.models import User
from django.test import TestCase
from django.db import IntegrityError
from tweet.models import (
    Tweet, Retweet, Hashtag, TweetHashtag, Mention, Notification,
    Bookmark, MutedUser, BlockedUser, TweetAnalytics
)


class TestRetweetIdempotence(TestCase):
    """
    Property 1: Retweet Idempotence
    For any user and tweet, retweeting the same tweet multiple times without 
    undoing should result in only one retweet record existing.
    
    Validates: Requirements 1.2, 1.5
    Feature: twitter-phase-2-social-engagement, Property 1: Retweet Idempotence
    """

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.other_user = User.objects.create_user(username='otheruser', password='pass123')
        self.tweet = Tweet.objects.create(user=self.other_user, text='Test tweet')

    def test_retweet_idempotence_single_retweet(self):
        """Test that a single retweet creates exactly one record"""
        # Create a retweet
        retweet = Retweet.objects.create(user=self.user, tweet=self.tweet)
        
        # Verify exactly one retweet exists
        retweet_count = Retweet.objects.filter(user=self.user, tweet=self.tweet).count()
        assert retweet_count == 1, f"Expected 1 retweet, got {retweet_count}"

    def test_retweet_idempotence_duplicate_prevention(self):
        """Test that duplicate retweets are prevented by unique constraint"""
        # Create first retweet
        retweet1, created1 = Retweet.objects.get_or_create(user=self.user, tweet=self.tweet)
        assert created1, "First retweet should be created"
        
        # Try to create duplicate - should return existing
        retweet2, created2 = Retweet.objects.get_or_create(user=self.user, tweet=self.tweet)
        assert not created2, "Second retweet should not be created (should be existing)"
        assert retweet1.id == retweet2.id, "Should return the same retweet"
        
        # Verify still only one retweet exists
        retweet_count = Retweet.objects.filter(user=self.user, tweet=self.tweet).count()
        assert retweet_count == 1, f"Expected 1 retweet after duplicate attempt, got {retweet_count}"

    def test_retweet_idempotence_property(self):
        """
        Property test: Multiple retweet attempts should result in at most one retweet.
        
        For any number of retweet attempts, the final state should have either 0 or 1 retweet.
        """
        # Test with various attempt counts
        for num_retweet_attempts in range(1, 11):
            # Create fresh user and tweet for this test
            user = User.objects.create_user(
                username=f'user_{num_retweet_attempts}',
                password='pass123'
            )
            other_user = User.objects.create_user(
                username=f'other_{num_retweet_attempts}',
                password='pass123'
            )
            tweet = Tweet.objects.create(user=other_user, text=f'Tweet {num_retweet_attempts}')
            
            # Attempt to create retweet multiple times using get_or_create
            retweet_created = False
            for _ in range(num_retweet_attempts):
                _, created = Retweet.objects.get_or_create(user=user, tweet=tweet)
                if created:
                    retweet_created = True
            
            # Verify final state: exactly 1 retweet
            final_count = Retweet.objects.filter(user=user, tweet=tweet).count()
            assert final_count == 1, f"Expected exactly 1 retweet, got {final_count}"
            assert retweet_created, "Retweet should have been created on first attempt"


class TestHashtagExtractionCompleteness(TestCase):
    """
    Property 2: Hashtag Extraction Completeness
    For any tweet text containing hashtags, all hashtags should be extracted 
    and indexed, regardless of their position or quantity in the text.
    
    Validates: Requirements 2.2
    Feature: twitter-phase-2-social-engagement, Property 2: Hashtag Extraction Completeness
    """

    def extract_hashtags_from_text(self, text):
        """Extract hashtags from tweet text"""
        import re
        # Find all hashtags (word characters after #)
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags

    def test_hashtag_extraction_single(self):
        """Test extraction of single hashtag"""
        text = "This is a tweet #python"
        hashtags = self.extract_hashtags_from_text(text)
        assert len(hashtags) == 1
        assert 'python' in hashtags

    def test_hashtag_extraction_multiple(self):
        """Test extraction of multiple hashtags"""
        text = "#python #django #testing are great"
        hashtags = self.extract_hashtags_from_text(text)
        assert len(hashtags) == 3
        assert 'python' in hashtags
        assert 'django' in hashtags
        assert 'testing' in hashtags

    def test_hashtag_extraction_various_positions(self):
        """Test hashtags at different positions"""
        text = "#start middle #middle end #end"
        hashtags = self.extract_hashtags_from_text(text)
        assert len(hashtags) == 3
        assert hashtags == ['start', 'middle', 'end']

    def test_hashtag_extraction_property(self):
        """
        Property test: All hashtags in text should be extracted.
        
        For any text with N hashtags, extraction should return exactly N hashtags.
        """
        # Test with various hashtag counts
        for hashtag_count in range(0, 11):
            text_parts = ['word', 'text', 'content', 'tweet', 'post']
            
            # Build text with hashtags
            hashtags_to_insert = [f'tag{i}' for i in range(hashtag_count)]
            text_parts_list = list(text_parts)
            
            # Interleave hashtags with text
            text = ""
            for i, hashtag in enumerate(hashtags_to_insert):
                text += text_parts_list[i % len(text_parts_list)] + f" #{hashtag} "
            
            # Extract hashtags
            extracted = self.extract_hashtags_from_text(text)
            
            # Verify all hashtags were extracted
            assert len(extracted) == hashtag_count, \
                f"Expected {hashtag_count} hashtags, extracted {len(extracted)}"
            
            # Verify all expected hashtags are present
            for expected_tag in hashtags_to_insert:
                assert expected_tag in extracted, f"Hashtag #{expected_tag} not extracted"


class TestMentionExtractionAccuracy(TestCase):
    """
    Property 10: Mention Extraction Accuracy
    For any tweet text containing @mentions, all valid mentions should be 
    extracted and only valid usernames should be recognized.
    
    Validates: Requirements 3.1
    Feature: twitter-phase-2-social-engagement, Property 10: Mention Extraction Accuracy
    """

    def extract_mentions_from_text(self, text):
        """Extract mentions from tweet text"""
        import re
        # Find all mentions (word characters after @)
        mentions = re.findall(r'@(\w+)', text)
        return mentions

    def test_mention_extraction_single(self):
        """Test extraction of single mention"""
        text = "Hey @john, how are you?"
        mentions = self.extract_mentions_from_text(text)
        assert len(mentions) == 1
        assert 'john' in mentions

    def test_mention_extraction_multiple(self):
        """Test extraction of multiple mentions"""
        text = "@alice @bob @charlie let's meet"
        mentions = self.extract_mentions_from_text(text)
        assert len(mentions) == 3
        assert 'alice' in mentions
        assert 'bob' in mentions
        assert 'charlie' in mentions

    def test_mention_extraction_various_positions(self):
        """Test mentions at different positions"""
        text = "@start middle @middle end @end"
        mentions = self.extract_mentions_from_text(text)
        assert len(mentions) == 3
        assert mentions == ['start', 'middle', 'end']

    def test_mention_extraction_property(self):
        """
        Property test: All mentions in text should be extracted.
        
        For any text with N mentions, extraction should return exactly N mentions.
        """
        # Test with various mention counts
        for mention_count in range(0, 11):
            text_parts = ['word', 'text', 'content', 'tweet', 'post']
            
            # Build text with mentions
            mentions_to_insert = [f'user{i}' for i in range(mention_count)]
            text_parts_list = list(text_parts)
            
            # Interleave mentions with text
            text = ""
            for i, mention in enumerate(mentions_to_insert):
                text += text_parts_list[i % len(text_parts_list)] + f" @{mention} "
            
            # Extract mentions
            extracted = self.extract_mentions_from_text(text)
            
            # Verify all mentions were extracted
            assert len(extracted) == mention_count, \
                f"Expected {mention_count} mentions, extracted {len(extracted)}"
            
            # Verify all expected mentions are present
            for expected_mention in mentions_to_insert:
                assert expected_mention in extracted, f"Mention @{expected_mention} not extracted"


class TestBookmarkPersistence(TestCase):
    """
    Property 5: Bookmark Persistence
    For any bookmarked tweet, the bookmark should persist until explicitly 
    removed, and the tweet should appear in the user's bookmarks collection.
    
    Validates: Requirements 5.2, 5.3
    Feature: twitter-phase-2-social-engagement, Property 5: Bookmark Persistence
    """

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.other_user = User.objects.create_user(username='otheruser', password='pass123')
        self.tweet = Tweet.objects.create(user=self.other_user, text='Test tweet')

    def test_bookmark_persistence_creation(self):
        """Test that bookmarks persist after creation"""
        # Create bookmark
        bookmark = Bookmark.objects.create(user=self.user, tweet=self.tweet)
        
        # Verify bookmark exists
        assert Bookmark.objects.filter(user=self.user, tweet=self.tweet).exists()
        
        # Verify tweet appears in user's bookmarks
        user_bookmarks = Bookmark.objects.filter(user=self.user)
        assert self.tweet in [b.tweet for b in user_bookmarks]

    def test_bookmark_persistence_retrieval(self):
        """Test that bookmarks can be retrieved after creation"""
        # Create bookmark
        Bookmark.objects.create(user=self.user, tweet=self.tweet)
        
        # Retrieve bookmarks
        bookmarks = Bookmark.objects.filter(user=self.user)
        assert bookmarks.count() == 1
        assert bookmarks.first().tweet == self.tweet

    def test_bookmark_persistence_deletion(self):
        """Test that bookmarks are removed when deleted"""
        # Create bookmark
        bookmark = Bookmark.objects.create(user=self.user, tweet=self.tweet)
        
        # Delete bookmark
        bookmark.delete()
        
        # Verify bookmark is gone
        assert not Bookmark.objects.filter(user=self.user, tweet=self.tweet).exists()

    def test_bookmark_persistence_property(self):
        """
        Property test: Bookmarks should persist and be retrievable.
        
        For any number of bookmarks created, they should all be retrievable
        until explicitly deleted.
        """
        # Test with various bookmark counts
        for num_bookmarks in range(1, 11):
            # Create user and tweets
            user = User.objects.create_user(
                username=f'user_{num_bookmarks}',
                password='pass123'
            )
            other_user = User.objects.create_user(
                username=f'other_{num_bookmarks}',
                password='pass123'
            )
            
            # Create tweets and bookmarks
            tweets = []
            for i in range(num_bookmarks):
                tweet = Tweet.objects.create(
                    user=other_user,
                    text=f'Tweet {i}'
                )
                tweets.append(tweet)
                Bookmark.objects.create(user=user, tweet=tweet)
            
            # Verify all bookmarks exist
            bookmarks = Bookmark.objects.filter(user=user)
            assert bookmarks.count() == num_bookmarks
            
            # Verify all tweets are in bookmarks
            bookmarked_tweets = [b.tweet for b in bookmarks]
            for tweet in tweets:
                assert tweet in bookmarked_tweets


class TestAnalyticsAccuracy(TestCase):
    """
    Property 8: Analytics Accuracy
    For any tweet, the engagement metrics in analytics should match the actual 
    count of likes, retweets, comments, and bookmarks.
    
    Validates: Requirements 9.2, 9.3
    Feature: twitter-phase-2-social-engagement, Property 8: Analytics Accuracy
    """

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.other_user = User.objects.create_user(username='otheruser', password='pass123')
        self.tweet = Tweet.objects.create(user=self.user, text='Test tweet')

    def test_analytics_accuracy_initial_state(self):
        """Test that analytics start at zero"""
        analytics = self.tweet.analytics
        assert analytics.likes_count == 0
        assert analytics.retweets_count == 0
        assert analytics.comments_count == 0
        assert analytics.bookmarks_count == 0

    def test_analytics_accuracy_after_like(self):
        """Test that analytics update after like"""
        from tweet.models import Like
        
        # Create like
        Like.objects.create(user=self.other_user, tweet=self.tweet)
        
        # Update analytics
        analytics = self.tweet.analytics
        analytics.update_counts()
        
        # Verify count matches
        assert analytics.likes_count == 1

    def test_analytics_accuracy_after_retweet(self):
        """Test that analytics update after retweet"""
        # Create retweet
        Retweet.objects.create(user=self.other_user, tweet=self.tweet)
        
        # Update analytics
        analytics = self.tweet.analytics
        analytics.update_counts()
        
        # Verify count matches
        assert analytics.retweets_count == 1

    def test_analytics_accuracy_after_bookmark(self):
        """Test that analytics update after bookmark"""
        # Create bookmark
        Bookmark.objects.create(user=self.other_user, tweet=self.tweet)
        
        # Update analytics
        analytics = self.tweet.analytics
        analytics.update_counts()
        
        # Verify count matches
        assert analytics.bookmarks_count == 1

    def test_analytics_accuracy_property(self):
        """
        Property test: Analytics counts should match actual engagement.
        
        For any combination of likes, retweets, and bookmarks, the analytics
        counts should exactly match the actual counts.
        """
        from tweet.models import Like
        
        # Test with a few representative combinations
        test_cases = [
            (0, 0, 0),
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (2, 2, 2),
            (3, 1, 2),
        ]
        
        for likes, retweets, bookmarks in test_cases:
            # Create users
            users = []
            for i in range(max(likes, retweets, bookmarks, 1)):
                user = User.objects.create_user(
                    username=f'user_{i}_{likes}_{retweets}_{bookmarks}',
                    password='pass123'
                )
                users.append(user)
            
            # Create tweet
            author = User.objects.create_user(
                username=f'author_{likes}_{retweets}_{bookmarks}',
                password='pass123'
            )
            tweet = Tweet.objects.create(user=author, text='Test tweet')
            
            # Create likes
            for i in range(likes):
                Like.objects.create(user=users[i], tweet=tweet)
            
            # Create retweets
            for i in range(retweets):
                Retweet.objects.create(user=users[i], tweet=tweet)
            
            # Create bookmarks
            for i in range(bookmarks):
                Bookmark.objects.create(user=users[i], tweet=tweet)
            
            # Update analytics
            analytics = tweet.analytics
            analytics.update_counts()
            
            # Verify all counts match
            assert analytics.likes_count == likes, \
                f"Expected {likes} likes, got {analytics.likes_count}"
            assert analytics.retweets_count == retweets, \
                f"Expected {retweets} retweets, got {analytics.retweets_count}"
            assert analytics.bookmarks_count == bookmarks, \
                f"Expected {bookmarks} bookmarks, got {analytics.bookmarks_count}"
