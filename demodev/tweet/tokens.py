from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Generate secure tokens for email verification"""
    
    def _make_hash_value(self, user, timestamp):
        """Create hash value based on user pk, timestamp, and active status"""
        return str(user.pk) + str(timestamp) + str(user.is_active)


email_verification_token = EmailVerificationTokenGenerator()
