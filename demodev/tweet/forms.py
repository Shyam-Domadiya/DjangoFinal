from django import forms
from .models import Tweet, UserProfile, Media
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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
