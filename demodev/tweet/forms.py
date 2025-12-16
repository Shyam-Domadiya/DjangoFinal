from django import forms
from .models import Tweet, UserProfile, Media
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class TweetForm(forms.ModelForm):
    media_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text='Comma-separated list of media IDs to attach to this tweet'
    )
    
    class Meta:
        model = Tweet
        fields = ['text', 'photo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate media_ids with existing media
        if self.instance.pk:
            existing_media_ids = list(self.instance.media.values_list('id', flat=True))
            if existing_media_ids:
                self.fields['media_ids'].initial = ','.join(map(str, existing_media_ids))
    
    def clean_media_ids(self):
        """Validate media IDs"""
        media_ids_str = self.cleaned_data.get('media_ids', '').strip()
        
        if not media_ids_str:
            return []
        
        try:
            media_ids = [int(mid.strip()) for mid in media_ids_str.split(',') if mid.strip()]
            return media_ids
        except ValueError:
            raise forms.ValidationError('Invalid media IDs provided.')
    
    def save(self, commit=True):
        """Save the tweet with media"""
        tweet = super().save(commit=False)
        
        if commit:
            tweet.save()
            
            # Handle media association
            media_ids = self.cleaned_data.get('media_ids', [])
            if media_ids:
                # Get media objects belonging to the tweet's user
                media_objects = Media.objects.filter(id__in=media_ids, user=tweet.user)
                tweet.media.set(media_objects)
            else:
                # Clear media if none provided
                tweet.media.clear()
        
        return tweet
        
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ('username','email','password1','password2')


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    
    class Meta:
        model = UserProfile
        fields = ['display_name', 'bio', 'profile_picture']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your display name',
                'maxlength': '100'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell us about yourself',
                'rows': 4,
                'maxlength': '500'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_display_name(self):
        """Validate display name"""
        display_name = self.cleaned_data.get('display_name', '').strip()
        if display_name and len(display_name) > 100:
            raise forms.ValidationError('Display name must be 100 characters or less.')
        return display_name
    
    def clean_bio(self):
        """Validate bio"""
        bio = self.cleaned_data.get('bio', '').strip()
        if bio and len(bio) > 500:
            raise forms.ValidationError('Bio must be 500 characters or less.')
        return bio
    
    def clean_profile_picture(self):
        """Validate profile picture file"""
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Profile picture must be less than 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if profile_picture.content_type not in allowed_types:
                raise forms.ValidationError('Only JPEG, PNG, and GIF images are allowed.')
        
        return profile_picture




class MediaUploadForm(forms.ModelForm):
    """Form for uploading media files with validation"""
    
    class Meta:
        model = Media
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif',
                'id': 'media-upload-input'
            })
        }
    
    def clean_file(self):
        """Validate media file type and size"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if file.size > max_size:
                raise forms.ValidationError(
                    f'File size must be less than 5MB. Your file is {file.size / (1024*1024):.2f}MB.'
                )
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if file.content_type not in allowed_types:
                raise forms.ValidationError(
                    'Only JPEG, PNG, and GIF images are allowed. '
                    f'Your file type is {file.content_type}.'
                )
        
        return file






# ============================================================================
# PASSWORD RESET FORMS - PRODUCTION GRADE WITH HTTPS SUPPORT
# ============================================================================

class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with enhanced validation and security.
    Supports HTTPS protocol for secure password reset links.
    """
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email address',
            'autocomplete': 'email',
            'required': True,
        })
    )
    
    def clean_email(self):
        """Validate email exists in the system"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('Email address is required.')
        
        # Check if user with this email exists
        if not User.objects.filter(email=email).exists():
            raise ValidationError(
                'No user account found with this email address. '
                'Please check and try again or register a new account.'
            )
        
        return email
    
    def save(self, request, **kwargs):
        """
        Generate password reset email with HTTPS support.
        
        Args:
            request: Django request object (used to determine protocol)
            **kwargs: Additional arguments
        
        Returns:
            Email address of the user
        """
        email = self.cleaned_data["email"]
        
        try:
            user = User.objects.get(email=email)
            
            # Import here to avoid circular imports
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.template.loader import render_to_string
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            # Generate secure token and encoded UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Determine protocol (HTTPS or HTTP)
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            
            # Build password reset link with HTTPS support
            reset_link = f"{protocol}://{domain}/reset/{uid}/{token}/"
            
            # Prepare email context
            context = {
                'user': user,
                'reset_link': reset_link,
                'protocol': protocol,
                'domain': domain,
                'uid': uid,
                'token': token,
            }
            
            # Render email template
            subject = "🔐 Reset Your FlexiBrain Password"
            message = render_to_string(
                'password/password_reset_email.html',
                context
            )
            
            # Send email
            email_message = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email_message.content_subtype = 'html'  # Send as HTML email
            email_message.send(fail_silently=False)
            
            return email
        
        except User.DoesNotExist:
            # Silently fail for security (don't reveal if email exists)
            return email
        except Exception as e:
            # Log the error but don't expose details to user
            import logging
            logger = logging.getLogger('tweet')
            logger.error(f"Error sending password reset email: {str(e)}", exc_info=True)
            raise ValidationError(
                'An error occurred while sending the password reset email. '
                'Please try again later.'
            )


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form with enhanced validation and security.
    Used after user clicks the password reset link.
    """
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password',
            'autocomplete': 'new-password',
            'required': True,
        }),
        help_text='Password must be at least 8 characters long.'
    )
    
    new_password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password',
            'autocomplete': 'new-password',
            'required': True,
        })
    )
    
    def clean_new_password1(self):
        """Validate new password strength"""
        password = self.cleaned_data.get('new_password1')
        
        if not password:
            raise ValidationError('Password is required.')
        
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for at least one lowercase letter
        if not any(char.islower() for char in password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise ValidationError('Password must contain at least one number.')
        
        # Check for at least one special character
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        if not any(char in special_chars for char in password):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*).')
        
        return password
    
    def clean_new_password2(self):
        """Validate password confirmation"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('The passwords do not match. Please try again.')
        
        return password2
    
    def save(self, commit=True):
        """Save the new password"""
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Log password change
            import logging
            logger = logging.getLogger('tweet')
            logger.info(f"Password reset successful for user: {user.username}", extra={'user_id': user.id})
        
        return user
