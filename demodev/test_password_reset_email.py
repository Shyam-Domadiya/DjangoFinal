#!/usr/bin/env python
"""
Test script to verify password reset email functionality
This script tests if emails are being sent correctly to your mailbox
"""

import os
import django
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demodev.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

print("=" * 80)
print("PASSWORD RESET EMAIL TEST")
print("=" * 80)

# Test 1: Check email configuration
print("\n✅ TEST 1: Email Configuration")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test 2: Send test email
print("\n✅ TEST 2: Sending Test Email")
try:
    send_mail(
        subject='🧪 Test Email - Password Reset System',
        message='This is a test email to verify the password reset system is working correctly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['shyamdomadiya78@gmail.com'],
        fail_silently=False,
    )
    print("   ✅ Test email sent successfully!")
except Exception as e:
    print(f"   ❌ Error sending test email: {str(e)}")

# Test 3: Create test user and send password reset email
print("\n✅ TEST 3: Password Reset Email")
try:
    # Create or get test user
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'shyamdomadiya78@gmail.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        print(f"   ✅ Created test user: {test_user.username}")
    else:
        print(f"   ✅ Using existing test user: {test_user.username}")
    
    # Generate token and UID
    token = default_token_generator.make_token(test_user)
    uid = urlsafe_base64_encode(force_bytes(test_user.pk))
    
    print(f"   ✅ Generated token: {token[:20]}...")
    print(f"   ✅ Generated UID: {uid}")
    
    # Create password reset link
    reset_link = f"http://127.0.0.1:8000/reset/{uid}/{token}/"
    
    # Prepare email context
    context = {
        'user': test_user,
        'reset_link': reset_link,
        'protocol': 'http',
        'domain': '127.0.0.1:8000',
        'uid': uid,
        'token': token,
    }
    
    # Render email template
    subject = "🔐 Reset Your FlexiBrain Password"
    message = render_to_string('password/password_reset_email.html', context)
    
    # Send email
    email_message = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=['shyamdomadiya78@gmail.com'],
    )
    email_message.content_subtype = 'html'
    email_message.send(fail_silently=False)
    
    print("   ✅ Password reset email sent successfully!")
    print(f"   📧 Email sent to: shyamdomadiya78@gmail.com")
    print(f"   🔗 Reset link: {reset_link}")
    
except Exception as e:
    print(f"   ❌ Error sending password reset email: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ EMAIL TEST COMPLETE")
print("=" * 80)
print("\n📧 Check your email at: shyamdomadiya78@gmail.com")
print("   You should receive 2 emails:")
print("   1. Test email")
print("   2. Password reset email with reset link")
print("\n🔗 Password Reset Link Format:")
print("   http://127.0.0.1:8000/reset/<uid>/<token>/")
print("\n" + "=" * 80)
