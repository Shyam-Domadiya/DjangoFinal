from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


class OTPVerification(models.Model):
    """Model to store OTP for password reset and email verification"""
    OTP_TYPE_CHOICES = [
        ('password_reset', 'Password Reset'),
        ('email_verification', 'Email Verification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, default='password_reset')
    email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['email', '-created_at']),
            models.Index(fields=['is_verified', 'expires_at']),
        ]
    
    def __str__(self):
        return f'OTP for {self.user.username} - {self.otp_type}'
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not verified)"""
        return not self.is_expired() and not self.is_verified
    
    def verify_otp(self, otp_code):
        """Verify the OTP code"""
        if self.is_expired():
            return False, 'OTP has expired'
        
        if self.is_verified:
            return False, 'OTP has already been verified'
        
        if self.attempts >= self.max_attempts:
            return False, 'Maximum attempts exceeded'
        
        self.attempts += 1
        self.save()
        
        if self.otp_code == otp_code:
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save()
            return True, 'OTP verified successfully'
        
        return False, f'Invalid OTP. Attempts remaining: {self.max_attempts - self.attempts}'
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_otp(user, otp_type='password_reset', expiry_minutes=10):
        """Create a new OTP for the user"""
        # Invalidate previous OTPs of the same type
        OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False
        ).delete()
        
        otp_code = OTPVerification.generate_otp()
        expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        
        otp = OTPVerification.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type,
            email=user.email,
            expires_at=expires_at
        )
        
        return otp
