# Step-by-Step Gmail Setup for Real-Time OTP

## Complete Guide with Examples

### Step 1: Enable 2-Factor Authentication

1. Open: https://myaccount.google.com/
2. Click **"Security"** (left sidebar)
3. Scroll to **"2-Step Verification"**
4. Click **"Get Started"**
5. Follow prompts:
   - Enter your password
   - Choose verification method (phone)
   - Enter verification code
   - Click "Turn On"

### Step 2: Generate App Password

1. Open: https://myaccount.google.com/apppasswords
2. You should see a dropdown menu
3. Select:
   - App: **"Mail"**
   - Device: **"Windows Computer"** (or your device)
4. Click **"Generate"**
5. Google shows a 16-character password:
   ```
   abcd efgh ijkl mnop
   ```
6. **Copy this exactly** (including spaces)

### Step 3: Update Django Settings

Open: `demodev/demodev/settings.py`

Find this section:
```python
# Email Configuration for Password Reset OTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Replace with your Gmail address
EMAIL_HOST_PASSWORD = 'your-app-password'  # Replace with your Gmail app password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'  # Replace with your Gmail address
```

Replace with your actual values:

**Example 1:**
```python
EMAIL_HOST_USER = 'john.doe@gmail.com'
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # Exactly as shown by Google
DEFAULT_FROM_EMAIL = 'john.doe@gmail.com'
```

**Example 2:**
```python
EMAIL_HOST_USER = 'myname@gmail.com'
EMAIL_HOST_PASSWORD = 'wxyz abcd efgh ijkl'  # Your app password
DEFAULT_FROM_EMAIL = 'myname@gmail.com'
```

### Step 4: Restart Django

Stop the current Django server (Ctrl+C) and restart:
```bash
python manage.py runserver
```

### Step 5: Test Email Sending

Open Django shell:
```bash
python manage.py shell
```

Run this code:
```python
from django.core.mail import send_mail
from django.conf import settings

# Send test email
send_mail(
    subject='Test OTP Email',
    message='Your OTP is: 123456\n\nThis OTP will expire in 10 minutes.',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-email@gmail.com'],
    fail_silently=False
)

print("✅ Email sent successfully!")
```

**Expected output:**
```
✅ Email sent successfully!
```

**Check your Gmail inbox** - you should receive the test email!

### Step 6: Test Password Reset Flow

1. Go to: http://127.0.0.1:8000/register/
2. Create a test account:
   - Username: `testuser`
   - Email: `your-email@gmail.com` (your real Gmail)
   - Password: `TestPassword123`

3. Go to: http://127.0.0.1:8000/login/
4. Click **"Forgot your password?"**
5. Enter your email: `your-email@gmail.com`
6. Click **"Continue"**
7. Select **"Email"** method
8. Click **"Send OTP"**
9. **Check your Gmail inbox** - OTP should arrive in seconds!
10. Copy the OTP from the email
11. Enter OTP on the verification page
12. Set new password
13. Login with new password ✅

---

## 🔍 Troubleshooting

### Error: "SMTPAuthenticationError: 535 5.7.8 Username and password not accepted"

**Cause:** Wrong password or 2FA not enabled

**Fix:**
1. Make sure 2FA is enabled: https://myaccount.google.com/security
2. Generate new app password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password exactly (with spaces)
4. Update settings.py
5. Restart Django

### Error: "SMTPNotSupportedError: SMTP AUTH extension not supported"

**Cause:** TLS not enabled

**Fix:**
```python
EMAIL_USE_TLS = True  # Make sure this is True
```

### Error: "Connection refused" or "Connection timed out"

**Cause:** Gmail SMTP server not reachable

**Fix:**
1. Check internet connection
2. Make sure EMAIL_HOST = 'smtp.gmail.com'
3. Make sure EMAIL_PORT = 587
4. Try again

### Email not arriving

**Cause:** Email might be in spam folder

**Fix:**
1. Check Gmail spam folder
2. Mark as "Not spam"
3. Try sending again

---

## ✅ Verification Steps

After setup, verify each step:

- [ ] 2FA enabled on Gmail account
- [ ] App password generated (16 characters)
- [ ] settings.py updated with correct credentials
- [ ] Django restarted
- [ ] Test email sent successfully from shell
- [ ] Test email received in Gmail inbox
- [ ] Password reset flow works end-to-end
- [ ] OTP received in real-time

---

## 📧 Email Format

When user requests OTP, they'll receive:

```
From: noreply@tweetapp.com
To: user@gmail.com
Subject: Password Reset OTP

Your OTP for password reset is: 123456

This OTP will expire in 10 minutes.
```

---

## 🎯 Next Steps

After Gmail is working:

1. **Optional:** Set up Twilio for SMS
   - See: `.kiro/STEP_BY_STEP_TWILIO_SETUP.md`

2. **Optional:** Add rate limiting
   - Prevent brute force attacks

3. **Optional:** Add logging
   - Track OTP delivery

4. **Deploy:** Move to production
   - Use environment variables for credentials

---

## 💡 Tips

1. **Keep app password safe** - don't share it
2. **Use environment variables** in production
3. **Test before deploying** to production
4. **Monitor email delivery** for issues
5. **Set up alerts** for failed deliveries

---

## 🔐 Security Notes

- App passwords are specific to your account
- They only work with 2FA enabled
- Regenerate if you suspect compromise
- Never commit to Git
- Use environment variables in production

---

**Status**: ✅ **READY TO SETUP**

Follow the steps above and you'll have real-time Gmail OTP delivery!
