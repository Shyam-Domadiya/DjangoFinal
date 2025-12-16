from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
import logging

from .forgot_password_forms import ForgotPasswordForm, ResetPasswordForm

logger = logging.getLogger('tweet')


@require_http_methods(["GET", "POST"])
def forgot_password(request):
    """
    Handle forgot password request.
    User enters username and email.
    If both match, send password reset email.
    """
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']

                # Get user
                user = User.objects.get(email=email)

                # Generate token and uid
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Determine protocol (HTTPS or HTTP)
                # In development: use HTTP (Django dev server doesn't support HTTPS)
                # In production: use HTTPS (configured via SECURE_SSL_REDIRECT)
                if settings.DEBUG:
                    protocol = 'http'  # Development: always use HTTP
                else:
                    protocol = 'https' if request.is_secure() else 'http'  # Production: use HTTPS
                domain = request.get_host()

                # Build reset link
                reset_link = f"{protocol}://{domain}/reset-password/{uid}/{token}/"

                # Prepare email context
                context = {
                    'user': user,
                    'reset_link': reset_link,
                    'protocol': protocol,
                    'domain': domain,
                }

                # Render email
                subject = 'Password Reset Request'
                html_message = render_to_string('forgot_password/reset_email.html', context)
                
                # Create plain text version for better deliverability
                text_message = f"""
Password Reset Request

Hello {user.username},

We received a request to reset the password for your account. If you didn't make this request, you can safely ignore this email.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

Password Requirements:
- At least 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*)

Security Notice:
- Never share this link with anyone
- We will never ask for your password via email
- The link uses HTTPS encryption for your security

If you did not request a password reset, please ignore this email. Your account is secure.

Best regards,
The Support Team

© 2024 All rights reserved.
Protocol: {protocol.upper()}
Domain: {domain}
"""

                # Send email with both HTML and plain text (better deliverability)
                from django.core.mail import EmailMultiAlternatives
                
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )
                
                # Attach HTML version
                email_message.attach_alternative(html_message, "text/html")
                
                # Add anti-spam headers using extra_headers parameter
                email_message.extra_headers = {
                    'X-Priority': '3',
                    'X-MSMail-Priority': 'Normal',
                    'X-Mailer': 'Django',
                    'List-Unsubscribe': f'<{protocol}://{domain}/>',
                    'Reply-To': settings.DEFAULT_FROM_EMAIL,
                }
                
                email_message.send(fail_silently=False)

                logger.info(f"Password reset email sent to {user.email}")
                messages.success(
                    request,
                    'Password reset link has been sent to your email. Please check your inbox.'
                )
                return redirect('forgot_password_done')

            except User.DoesNotExist:
                logger.warning(f"Password reset attempt with non-existent user")
                messages.error(request, 'Username or email not found.')
            except Exception as e:
                logger.error(f"Error sending password reset email: {str(e)}", exc_info=True)
                messages.error(request, 'An error occurred. Please try again later.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, str(error))
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password/forgot_password.html', {'form': form})


@require_http_methods(["GET"])
def forgot_password_done(request):
    """Display confirmation message after password reset email is sent"""
    return render(request, 'forgot_password/forgot_password_done.html')


@require_http_methods(["GET", "POST"])
def reset_password(request, uidb64, token):
    """
    Handle password reset.
    Validate token and uid, then allow user to set new password.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        logger.warning(f"Invalid password reset attempt with uidb64: {uidb64}")

    # Validate token
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                try:
                    new_password = form.cleaned_data['new_password']

                    # Update password
                    user.set_password(new_password)
                    user.save()

                    logger.info(f"Password reset successful for user: {user.username}")
                    messages.success(
                        request,
                        'Your password has been reset successfully. You can now login with your new password.'
                    )
                    return redirect('reset_password_complete')

                except Exception as e:
                    logger.error(f"Error resetting password: {str(e)}", exc_info=True)
                    messages.error(request, 'An error occurred while resetting your password.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, str(error))
        else:
            form = ResetPasswordForm()

        return render(
            request,
            'forgot_password/reset_password.html',
            {
                'form': form,
                'validlink': True,
                'user': user,
            }
        )
    else:
        logger.warning(f"Invalid or expired password reset token")
        messages.error(
            request,
            'The password reset link is invalid or has expired. Please request a new one.'
        )
        return render(
            request,
            'forgot_password/reset_password.html',
            {'validlink': False}
        )


@require_http_methods(["GET"])
def reset_password_complete(request):
    """Display success message after password reset"""
    return render(request, 'forgot_password/reset_password_complete.html')
