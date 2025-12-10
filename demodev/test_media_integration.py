#!/usr/bin/env python
"""
Test script to verify media integration with tweet creation and editing
"""
import os
import sys
import django
import uuid

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demodev.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from PIL import Image
from io import BytesIO

from tweet.models import Tweet, Media
from tweet.forms import TweetForm


def get_unique_username():
    """Generate a unique username"""
    return f"testuser_{uuid.uuid4().hex[:8]}"


def create_test_image(name='test.jpg', size=(100, 100)):
    """Helper to create a test image"""
    img = Image.new('RGB', size, color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile(name, img_io.getvalue(), content_type='image/jpeg')


def test_media_form_integration():
    """Test that media can be integrated with tweet form"""
    print("\n=== Testing Media Form Integration ===")
    
    # Create test user
    user = User.objects.create_user(username=get_unique_username(), password='testpass')
    print(f"✓ Created test user: {user.username}")
    
    # Create test media
    media = Media.objects.create(
        user=user,
        file=create_test_image(),
        file_type='image'
    )
    print(f"✓ Created test media: {media.id}")
    
    # Test form with media_ids
    form_data = {
        'text': 'Test tweet with media',
        'media_ids': str(media.id),
        'scheduled_publish_time': ''
    }
    form = TweetForm(data=form_data)
    
    if form.is_valid():
        print("✓ Form is valid")
        
        # Save tweet
        tweet = form.save(commit=False)
        tweet.user = user
        tweet.save()
        form.save()
        
        # Verify media association
        if tweet.media.filter(id=media.id).exists():
            print(f"✓ Media successfully associated with tweet {tweet.id}")
            return True
        else:
            print("✗ Media not associated with tweet")
            return False
    else:
        print(f"✗ Form validation failed: {form.errors}")
        return False


def test_media_form_multiple_media():
    """Test that multiple media can be associated with a tweet"""
    print("\n=== Testing Multiple Media Integration ===")
    
    # Create test user
    user = User.objects.create_user(username=get_unique_username(), password='testpass')
    print(f"✓ Created test user: {user.username}")
    
    # Create multiple media files
    media_ids = []
    for i in range(3):
        media = Media.objects.create(
            user=user,
            file=create_test_image(f'test{i}.jpg'),
            file_type='image'
        )
        media_ids.append(media.id)
    print(f"✓ Created {len(media_ids)} media files")
    
    # Test form with multiple media
    form_data = {
        'text': 'Test tweet with multiple media',
        'media_ids': ','.join(map(str, media_ids)),
        'scheduled_publish_time': ''
    }
    form = TweetForm(data=form_data)
    
    if form.is_valid():
        print("✓ Form is valid")
        
        # Save tweet
        tweet = form.save(commit=False)
        tweet.user = user
        tweet.save()
        form.save()
        
        # Verify all media are associated
        associated_count = tweet.media.count()
        if associated_count == len(media_ids):
            print(f"✓ All {associated_count} media files associated with tweet")
            return True
        else:
            print(f"✗ Expected {len(media_ids)} media, got {associated_count}")
            return False
    else:
        print(f"✗ Form validation failed: {form.errors}")
        return False


def test_media_form_edit():
    """Test that media can be updated when editing a tweet"""
    print("\n=== Testing Media Edit Integration ===")
    
    # Create test user
    user = User.objects.create_user(username=get_unique_username(), password='testpass')
    print(f"✓ Created test user: {user.username}")
    
    # Create initial media
    media1 = Media.objects.create(
        user=user,
        file=create_test_image('test1.jpg'),
        file_type='image'
    )
    
    # Create tweet with initial media
    tweet = Tweet.objects.create(user=user, text='Original tweet')
    tweet.media.add(media1)
    print(f"✓ Created tweet with initial media")
    
    # Create new media
    media2 = Media.objects.create(
        user=user,
        file=create_test_image('test2.jpg'),
        file_type='image'
    )
    
    # Edit tweet with new media
    form_data = {
        'text': 'Updated tweet',
        'media_ids': str(media2.id),
        'scheduled_publish_time': ''
    }
    form = TweetForm(data=form_data, instance=tweet)
    
    if form.is_valid():
        print("✓ Form is valid")
        
        # Save edited tweet
        tweet = form.save(commit=False)
        tweet.save()
        form.save()
        
        # Verify media was updated
        if tweet.media.filter(id=media2.id).exists() and not tweet.media.filter(id=media1.id).exists():
            print(f"✓ Media successfully updated in tweet")
            return True
        else:
            print(f"✗ Media not properly updated")
            return False
    else:
        print(f"✗ Form validation failed: {form.errors}")
        return False


def test_media_form_clear():
    """Test that media can be cleared from a tweet"""
    print("\n=== Testing Media Clear Integration ===")
    
    # Create test user
    user = User.objects.create_user(username=get_unique_username(), password='testpass')
    print(f"✓ Created test user: {user.username}")
    
    # Create media
    media = Media.objects.create(
        user=user,
        file=create_test_image(),
        file_type='image'
    )
    
    # Create tweet with media
    tweet = Tweet.objects.create(user=user, text='Tweet with media')
    tweet.media.add(media)
    print(f"✓ Created tweet with media")
    
    # Edit tweet to remove media
    form_data = {
        'text': 'Tweet without media',
        'media_ids': '',
        'scheduled_publish_time': ''
    }
    form = TweetForm(data=form_data, instance=tweet)
    
    if form.is_valid():
        print("✓ Form is valid")
        
        # Save edited tweet
        tweet = form.save(commit=False)
        tweet.save()
        form.save()
        
        # Verify media was cleared
        if tweet.media.count() == 0:
            print(f"✓ Media successfully cleared from tweet")
            return True
        else:
            print(f"✗ Media not properly cleared")
            return False
    else:
        print(f"✗ Form validation failed: {form.errors}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("Media Integration Tests")
    print("=" * 50)
    
    results = []
    
    try:
        results.append(("Media Form Integration", test_media_form_integration()))
        results.append(("Multiple Media Integration", test_media_form_multiple_media()))
        results.append(("Media Edit Integration", test_media_form_edit()))
        results.append(("Media Clear Integration", test_media_form_clear()))
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        sys.exit(1)
