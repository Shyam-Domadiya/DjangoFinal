from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset - requires only email"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise ValidationError(
                    'No account found with this email address. Please check and try again.'
                )

        return cleaned_data


class ResetPasswordForm(forms.Form):
    """Form for resetting password with validation"""
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
        min_length=8,
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('Passwords do not match. Please try again.')

            # Password strength validation
            if not any(char.isupper() for char in new_password):
                raise ValidationError('Password must contain at least one uppercase letter.')

            if not any(char.islower() for char in new_password):
                raise ValidationError('Password must contain at least one lowercase letter.')

            if not any(char.isdigit() for char in new_password):
                raise ValidationError('Password must contain at least one number.')

            special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
            if not any(char in special_chars for char in new_password):
                raise ValidationError('Password must contain at least one special character (!@#$%^&*).')

        return cleaned_data
