"""
Test script for REST API endpoints
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demodev.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from tweet.models import UserProfile, Tweet, Media, TweetDraft

def test_api_endpoints():
    """Test all API endpoints"""
    client = Client()
    
    # Create test user or get existing
    user = User.objects.filter(username='testuser').first()
    if not user:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    else:
        # Update password to ensure it's correct
        user.set_password('testpass123')
        user.save()
    
    # Ensure profile exists
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.bio = 'Test bio'
    profile.display_name = 'Test User'
    profile.save()
    
    print("=" * 60)
    print("Testing REST API Endpoints")
    print("=" * 60)
    
    # Test 1: Get user profiles (unauthenticated)
    print("\n1. GET /api/profiles/ (unauthenticated)")
    response = client.get('/api/profiles/')
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "Should return 200 for unauthenticated GET"
    
    # Test 2: Get current user profile (authenticated)
    print("\n2. GET /api/profiles/me/ (authenticated)")
    client.login(username='testuser', password='testpass123')
    response = client.get('/api/profiles/me/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200 for authenticated GET"
    assert data['user']['username'] == 'testuser', "Should return correct user"
    
    # Test 3: Update user profile
    print("\n3. PATCH /api/profiles/testuser/ (update profile)")
    response = client.patch(
        '/api/profiles/testuser/',
        data=json.dumps({'bio': 'Updated bio', 'display_name': 'Updated Name'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200 for PATCH"
    assert data['bio'] == 'Updated bio', "Bio should be updated"
    
    # Test 4: Get profile statistics
    print("\n4. GET /api/profiles/testuser/statistics/")
    response = client.get('/api/profiles/testuser/statistics/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert 'follower_count' in data, "Should have follower_count"
    
    # Test 5: Create a tweet
    print("\n5. POST /api/tweets/ (create tweet)")
    response = client.post(
        '/api/tweets/',
        data=json.dumps({'text': 'Test tweet content'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 201, "Should return 201 for POST"
    tweet_id = data['id']
    
    # Test 6: Get tweets list
    print("\n6. GET /api/tweets/")
    response = client.get('/api/tweets/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response count: {len(data['results']) if 'results' in data else 'N/A'}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 7: Get tweet detail
    print(f"\n7. GET /api/tweets/{tweet_id}/")
    response = client.get(f'/api/tweets/{tweet_id}/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert data['text'] == 'Test tweet content', "Should return correct tweet"
    
    # Test 8: Like a tweet
    print(f"\n8. POST /api/tweets/{tweet_id}/like/")
    response = client.post(f'/api/tweets/{tweet_id}/like/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 201, "Should return 201"
    
    # Test 9: Get tweet likes
    print(f"\n9. GET /api/tweets/{tweet_id}/likes/")
    response = client.get(f'/api/tweets/{tweet_id}/likes/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert data['count'] == 1, "Should have 1 like"
    
    # Test 10: Add comment
    print(f"\n10. POST /api/tweets/{tweet_id}/add_comment/")
    response = client.post(
        f'/api/tweets/{tweet_id}/add_comment/',
        data=json.dumps({'text': 'Test comment'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 201, "Should return 201"
    
    # Test 11: Get tweet comments
    print(f"\n11. GET /api/tweets/{tweet_id}/comments/")
    response = client.get(f'/api/tweets/{tweet_id}/comments/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert data['count'] == 1, "Should have 1 comment"
    
    # Test 12: Update tweet
    print(f"\n12. PATCH /api/tweets/{tweet_id}/")
    response = client.patch(
        f'/api/tweets/{tweet_id}/',
        data=json.dumps({'text': 'Updated tweet content'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert data['text'] == 'Updated tweet content', "Tweet should be updated"
    assert data['is_edited'] == True, "Tweet should be marked as edited"
    
    # Test 13: Get edit history
    print(f"\n13. GET /api/tweets/{tweet_id}/edit_history/")
    response = client.get(f'/api/tweets/{tweet_id}/edit_history/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert data['count'] == 1, "Should have 1 edit"
    
    # Test 14: Create draft
    print("\n14. POST /api/drafts/")
    response = client.post(
        '/api/drafts/',
        data=json.dumps({'content': 'Draft content'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 201, "Should return 201"
    draft_id = data['id']
    
    # Test 15: Get current draft
    print("\n15. GET /api/drafts/current/")
    response = client.get('/api/drafts/current/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    assert data['content'] == 'Draft content', "Should return correct draft"
    
    # Test 16: Update draft
    print(f"\n16. PATCH /api/drafts/{draft_id}/")
    response = client.patch(
        f'/api/drafts/{draft_id}/',
        data=json.dumps({'content': 'Updated draft content'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 17: Search tweets
    print("\n17. GET /api/search/tweets/?q=test")
    response = client.get('/api/search/tweets/?q=test')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 18: Search users
    print("\n18. GET /api/search/users/?q=test")
    response = client.get('/api/search/users/?q=test')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 19: Combined search
    print("\n19. GET /api/search/all/?q=test")
    response = client.get('/api/search/all/?q=test')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 20: Get scheduled tweets
    print("\n20. GET /api/tweets/scheduled/")
    response = client.get('/api/tweets/scheduled/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 21: Delete draft
    print(f"\n21. DELETE /api/drafts/{draft_id}/")
    response = client.delete(f'/api/drafts/{draft_id}/')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 204, "Should return 204"
    
    # Test 22: Unlike tweet
    print(f"\n22. POST /api/tweets/{tweet_id}/unlike/")
    response = client.post(f'/api/tweets/{tweet_id}/unlike/')
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    assert response.status_code == 200, "Should return 200"
    
    # Test 23: Delete tweet
    print(f"\n23. DELETE /api/tweets/{tweet_id}/")
    response = client.delete(f'/api/tweets/{tweet_id}/')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 204, "Should return 204"
    
    print("\n" + "=" * 60)
    print("All API tests passed!")
    print("=" * 60)

if __name__ == '__main__':
    test_api_endpoints()
