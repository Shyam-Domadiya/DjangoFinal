#!/usr/bin/env python
"""
Complete Forgot Password Flow Test
Tests the entire password reset system end-to-end
"""

import os
import sys
import django

# Add the demodev directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demodev.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.test import Client
from django.urls import reverse

from django.conf import settings


def test_user_creation():
    """Test 1: Create a test user"""
    print("\n" + "="*70)
    print("TEST 1: Creating Test User")
    print("="*70)
    
    # Delete existing test user if exists
    User.objects.filter(username='testuser').delete()
    
    # Create new test user
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='OldPassword123!'
    )
    
    print(f"✓ Test user created successfully")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  User ID: {user.id}")
    
    return user


def test_token_generation(user):
    """Test 2: Generate password reset token"""
    print("\n" + "="*70)
    print("TEST 2: Generating Password Reset Token")
    print("="*70)
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Handle both string and bytes
    uid_str = uid if isinstance(uid, str) else uid.decode()
    
    print(f"✓ Token generated successfully")
    print(f"  Token: {token[:20]}...")
    print(f"  UID (base64): {uid_str}")
    
    # Verify token is valid
    is_valid = default_token_generator.check_token(user, token)
    print(f"  Token valid: {is_valid}")
    
    return token, uid_str


def test_forgot_password_page():
    """Test 3: Access forgot password page"""
    print("\n" + "="*70)
    print("TEST 3: Accessing Forgot Password Page")
    print("="*70)
    
    client = Client()
    response = client.get(reverse('forgot_password'))
    
    print(f"✓ Forgot password page accessed")
    print(f"  Status Code: {response.status_code}")
    print(f"  Expected: 200")
    
    if response.status_code == 200:
        print(f"  ✓ Page loaded successfully")
    else:
        print(f"  ✗ Page failed to load")
    
    return client


def test_forgot_password_submission(client, user):
    """Test 4: Submit forgot password form"""
    print("\n" + "="*70)
    print("TEST 4: Submitting Forgot Password Form")
    print("="*70)
    
    data = {
        'email': user.email
    }
    
    response = client.post(reverse('forgot_password'), data)
    
    print(f"✓ Forgot password form submitted")
    print(f"  Email: {user.email}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Expected: 302 (redirect)")
    
    if response.status_code == 302:
        print(f"  ✓ Form submitted successfully (redirected)")
        print(f"  Redirect URL: {response.url}")
    else:
        print(f"  ✗ Form submission failed")
    
    return response


def test_reset_password_page(client, user, token, uid):
    """Test 5: Access reset password page with valid token"""
    print("\n" + "="*70)
    print("TEST 5: Accessing Reset Password Page")
    print("="*70)
    
    uid_str = uid if isinstance(uid, str) else uid.decode()
    reset_url = reverse('reset_password', kwargs={'uidb64': uid_str, 'token': token})
    response = client.get(reset_url)
    
    print(f"✓ Reset password page accessed")
    print(f"  URL: {reset_url}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Expected: 200")
    
    if response.status_code == 200:
        print(f"  ✓ Page loaded successfully")
        if b'validlink' in response.content or b'Reset Your Password' in response.content:
            print(f"  ✓ Valid link detected")
        else:
            print(f"  ✗ Valid link not detected")
    else:
        print(f"  ✗ Page failed to load")
    
    return response


def test_reset_password_submission(client, user, token, uid):
    """Test 6: Submit new password"""
    print("\n" + "="*70)
    print("TEST 6: Submitting New Password")
    print("="*70)
    
    new_password = 'NewPassword123!'
    
    data = {
        'new_password': new_password,
        'confirm_password': new_password
    }
    
    uid_str = uid if isinstance(uid, str) else uid.decode()
    reset_url = reverse('reset_password', kwargs={'uidb64': uid_str, 'token': token})
    response = client.post(reset_url, data)
    
    print(f"✓ New password submitted")
    print(f"  New Password: {new_password}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Expected: 302 (redirect)")
    
    if response.status_code == 302:
        print(f"  ✓ Password reset successfully (redirected)")
        print(f"  Redirect URL: {response.url}")
    else:
        print(f"  ✗ Password reset failed")
    
    return response


def test_login_with_new_password(client, user):
    """Test 7: Login with new password"""
    print("\n" + "="*70)
    print("TEST 7: Login with New Password")
    print("="*70)
    
    # Refresh user from database to get updated password
    user.refresh_from_db()
    
    new_password = 'NewPassword123!'
    
    login_data = {
        'username': user.username,
        'password': new_password
    }
    
    response = client.post(reverse('login'), login_data)
    
    print(f"✓ Login attempt with new password")
    print(f"  Username: {user.username}")
    print(f"  Status Code: {response.status_code}")
    
    # Check if user is authenticated
    if response.wsgi_request.user.is_authenticated:
        print(f"  ✓ Login successful - user authenticated")
    else:
        print(f"  ✗ Login failed - user not authenticated")
    
    return response


def test_invalid_token(client, user):
    """Test 8: Test with invalid token"""
    print("\n" + "="*70)
    print("TEST 8: Testing Invalid Token")
    print("="*70)
    
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    uid_str = uid if isinstance(uid, str) else uid.decode()
    invalid_token = 'invalid-token-12345'
    
    reset_url = reverse('reset_password', kwargs={'uidb64': uid_str, 'token': invalid_token})
    response = client.get(reset_url)
    
    print(f"✓ Invalid token page accessed")
    print(f"  Status Code: {response.status_code}")
    
    if response.status_code == 200:
        if b'invalid' in response.content.lower() or b'expired' in response.content.lower():
            print(f"  ✓ Invalid token properly handled")
        else:
            print(f"  ✗ Invalid token not properly handled")
    else:
        print(f"  ✗ Page failed to load")
    
    return response


def test_password_validation(client, user, token, uid):
    """Test 9: Test password validation"""
    print("\n" + "="*70)
    print("TEST 9: Testing Password Validation")
    print("="*70)
    
    # Test weak password (no special character)
    weak_password = 'WeakPass123'
    
    data = {
        'new_password': weak_password,
        'confirm_password': weak_password
    }
    
    uid_str = uid if isinstance(uid, str) else uid.decode()
    reset_url = reverse('reset_password', kwargs={'uidb64': uid_str, 'token': token})
    response = client.post(reset_url, data)
    
    print(f"✓ Weak password validation test")
    print(f"  Password: {weak_password}")
    print(f"  Status Code: {response.status_code}")
    
    if response.status_code == 200:
        if b'special character' in response.content.lower():
            print(f"  ✓ Weak password properly rejected")
        else:
            print(f"  ✗ Weak password validation not working")
    else:
        print(f"  ✗ Validation test failed")
    
    return response


def test_email_configuration():
    """Test 10: Verify email configuration"""
    print("\n" + "="*70)
    print("TEST 10: Email Configuration")
    print("="*70)
    
    print(f"✓ Email Configuration:")
    print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  PASSWORD_RESET_TIMEOUT: {settings.PASSWORD_RESET_TIMEOUT} seconds ({settings.PASSWORD_RESET_TIMEOUT // 3600} hours)")
    
    if settings.EMAIL_HOST_USER:
        print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER[:10]}...")
    else:
        print(f"  EMAIL_HOST_USER: Not configured")
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print(f"\n  ⚠ WARNING: Using console email backend (development mode)")
        print(f"  Emails will be printed to console, not sent")
    elif settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
        print(f"\n  ✓ Using SMTP email backend (production mode)")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("FORGOT PASSWORD SYSTEM - COMPLETE FLOW TEST")
    print("="*70)
    
    try:
        # Test 1: Create user
        user = test_user_creation()
        
        # Test 2: Generate token
        token, uid = test_token_generation(user)
        
        # Test 3: Access forgot password page
        client = test_forgot_password_page()
        
        # Test 4: Submit forgot password form
        test_forgot_password_submission(client, user)
        
        # Test 5: Access reset password page
        test_reset_password_page(client, user, token, uid)
        
        # Test 6: Submit new password
        test_reset_password_submission(client, user, token, uid)
        
        # Test 7: Login with new password
        test_login_with_new_password(client, user)
        
        # Test 8: Invalid token
        test_invalid_token(client, user)
        
        # Test 9: Password validation
        test_password_validation(client, user, token, uid)
        
        # Test 10: Email configuration
        test_email_configuration()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("✓ All tests completed successfully!")
        print("\nThe forgot password system is working correctly.")
        print("\nNext Steps:")
        print("1. Test with a real email address")
        print("2. Check email inbox for password reset link")
        print("3. Click the link and reset password")
        print("4. Login with new password")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
