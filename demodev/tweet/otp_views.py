from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from .models import OTPVerification
from .forms import ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
import logging

logger = logging.getLogger('tweet')


def forgot_password(request):
    """View to initiate password reset process"""
    if request.user.is_authenticated:
        return redirect('tweet_list')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Create OTP
                otp = OTPVerification.create_otp(user, otp_type='password_reset', expiry_minutes=10)
                
                # Send OTP via email
                subject = 'Password Reset OTP'
                message = f'''
Hello {user.first_name or user.username},

Your OTP for password reset is: {otp.otp_code}

This OTP will expire in 10 minutes.

If you did not request this, please ignore this email.

Best regards,
Tweet App Team
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                logger.info(f"Password reset OTP sent to {email}", extra={'user_id': user.id})
                messages.success(request, f'OTP sent to {email}. Please check your email.')
                
                # Redirect to OTP verification page
                return redirect('verify_otp', user_id=user.id)
            
            except User.DoesNotExist:
                logger.warning(f"Password reset attempt with non-existent email: {email}")
                # Don't reveal if email exists for security
                messages.info(request, 'If an account exists with this email, you will receive an OTP.')
                return redirect('login')
            
            except Exception as e:
                logger.error(f"Error sending OTP email: {str(e)}", exc_info=True)
                messages.error(request, 'An error occurred while sending the OTP. Please try again.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'forgot_password.html', {'form': form})


def verify_otp(request, user_id):
    """View to verify OTP"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    # Get the latest unverified OTP
    otp = OTPVerification.objects.filter(
        user=user,
        otp_type='password_reset',
        is_verified=False
    ).order_by('-created_at').first()
    
    if not otp:
        messages.error(request, 'No valid OTP found. Please request a new one.')
        return redirect('forgot_password')
    
    if otp.is_expired():
        messages.error(request, 'OTP has expired. Please request a new one.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            is_valid, message = otp.verify_otp(otp_code)
            
            if is_valid:
                logger.info(f"OTP verified for user {user.username}", extra={'user_id': user.id})
                messages.success(request, 'OTP verified successfully!')
                return redirect('reset_password', user_id=user.id)
            else:
                logger.warning(f"Invalid OTP attempt for user {user.username}", extra={'user_id': user.id})
                messages.error(request, message)
    else:
        form = OTPVerificationForm()
    
    # Calculate time remaining
    time_remaining = (otp.expires_at - timezone.now()).total_seconds()
    minutes_remaining = int(time_remaining // 60)
    seconds_remaining = int(time_remaining % 60)
    
    return render(request, 'verify_otp.html', {
        'form': form,
        'user': user,
        'otp': otp,
        'minutes_remaining': minutes_remaining,
        'seconds_remaining': seconds_remaining,
        'attempts_remaining': otp.max_attempts - otp.attempts
    })


def reset_password(request, user_id):
    """View to reset password after OTP verification"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    # Verify that OTP has been verified
    otp = OTPVerification.objects.filter(
        user=user,
        otp_type='password_reset',
        is_verified=True
    ).order_by('-verified_at').first()
    
    if not otp:
        messages.error(request, 'Please verify OTP first.')
        return redirect('forgot_password')
    
    # Check if OTP verification is recent (within 5 minutes)
    time_since_verification = (timezone.now() - otp.verified_at).total_seconds()
    if time_since_verification > 300:  # 5 minutes
        messages.error(request, 'OTP verification expired. Please request a new OTP.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            
            try:
                user.set_password(password)
                user.save()
                
                logger.info(f"Password reset successful for user {user.username}", extra={'user_id': user.id})
                messages.success(request, 'Password reset successfully! You can now login with your new password.')
                
                return redirect('login')
            
            except Exception as e:
                logger.error(f"Error resetting password for user {user.username}: {str(e)}", exc_info=True)
                messages.error(request, 'An error occurred while resetting the password. Please try again.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'reset_password.html', {
        'form': form,
        'user': user
    })


def resend_otp(request, user_id):
    """AJAX endpoint to resend OTP"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            
            # Check if user has a recent OTP
            recent_otp = OTPVerification.objects.filter(
                user=user,
                otp_type='password_reset',
                is_verified=False
            ).order_by('-created_at').first()
            
            # Allow resend only if previous OTP is expired or doesn't exist
            if recent_otp and not recent_otp.is_expired():
                time_remaining = (recent_otp.expires_at - timezone.now()).total_seconds()
                return JsonResponse({
                    'success': False,
                    'error': f'Please wait {int(time_remaining)} seconds before requesting a new OTP.'
                }, status=429)
            
            # Create new OTP
            otp = OTPVerification.create_otp(user, otp_type='password_reset', expiry_minutes=10)
            
            # Send OTP via email
            subject = 'Password Reset OTP (Resend)'
            message = f'''
Hello {user.first_name or user.username},

Your new OTP for password reset is: {otp.otp_code}

This OTP will expire in 10 minutes.

If you did not request this, please ignore this email.

Best regards,
Tweet App Team
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            logger.info(f"OTP resent to {user.email}", extra={'user_id': user.id})
            
            return JsonResponse({
                'success': True,
                'message': 'OTP resent successfully!'
            })
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found.'
            }, status=404)
        
        except Exception as e:
            logger.error(f"Error resending OTP: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while resending the OTP.'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
