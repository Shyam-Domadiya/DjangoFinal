# OTP System - Usage Guide

## ✅ Fixed: Email Backend Configuration

The OTP system is now configured to save emails to files so you can easily see the OTP codes.

### Email Storage Location
```
demodev/sent_emails/
```

All emails (including OTP codes) are saved as text files in this directory.

## 🚀 How to Use the Password Reset System

### Step 1: Register a User
1. Go to `http://127.0.0.1:8000/register/`
2. Create an account:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `TestPassword123`
   - Phone (optional): Leave blank or enter `+1234567890`

### Step 2: Test Forgot Password
1. Go to `http://127.0.0.1:8000/login/`
2. Click **"Forgot your password?"** link
3. Enter your email: `test@example.com`
4. Click **"Continue"**

### Step 3: Choose Delivery Method
1. Select **"Email"** (SMS requires phone number)
2. Click **"Send OTP"**
3. You'll see: "OTP sent to test@example.com"

### Step 4: Find Your OTP
1. Open file explorer
2. Navigate to: `demodev/sent_emails/`
3. Open the latest `.txt` file
4. Look for the OTP code (6 digits)

**Example email content:**
```
Subject: Password Reset OTP
From: noreply@tweetapp.com
To: test@example.com

Your OTP for password reset is: 123456

This OTP will expire in 10 minutes.
```

### Step 5: Verify OTP
1. Go back to browser (should be on verify OTP page)
2. Enter the 6-digit OTP from the email file
3. Click **"Verify OTP"**
4. You'll see: "OTP verified successfully!"

### Step 6: Reset Password
1. Enter new password: `NewPassword456`
2. Confirm password: `NewPassword456`
3. Click **"Reset Password"**
4. You'll be redirected to login page

### Step 7: Login with New Password
1. Username: `testuser`
2. Password: `NewPassword456`
3. Click **"Login"**
4. Should successfully login!

## 📁 Email Files Location

**Path:** `demodev/sent_emails/`

Each email is saved as a separate `.txt` file with timestamp.

**To find the latest OTP:**
1. Open `demodev/sent_emails/` folder
2. Sort by "Date Modified" (newest first)
3. Open the top file
4. Copy the 6-digit OTP code

## 🔍 Troubleshooting

### Issue: No files in sent_emails folder
**Solution:**
1. Check that `EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'` in settings.py
2. Restart Django server
3. Try sending OTP again

### Issue: OTP expired
**Solution:**
- OTP expires after 10 minutes
- Go back to forgot password and request a new OTP

### Issue: Invalid OTP error
**Solution:**
- Make sure you copied the OTP correctly (6 digits only)
- Check the latest email file in sent_emails folder
- OTP must be entered within 10 minutes

### Issue: "No phone number on file" when choosing SMS
**Solution:**
- SMS requires a phone number during registration
- Use Email method instead, or
- Register again with a phone number

## 📧 Email Configuration Options

### Current (Development - File Based)
```python
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')
```
✅ Emails saved to files
✅ Easy to view OTP codes
✅ No external service needed

### Console Output (Alternative)
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
✅ Emails printed to terminal/console
✅ No files created
⚠️ Output may not be visible in browser

### Production (Gmail)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```
✅ Real emails sent
✅ Production ready
⚠️ Requires Gmail account setup

## 🔐 Security Features

- ✅ OTP expires after 10 minutes
- ✅ 6-digit random generation
- ✅ Single-use verification
- ✅ Session-based flow (can't skip steps)
- ✅ CSRF protection
- ✅ Email validation
- ✅ Password validation (min 8 chars)

## 📱 SMS Integration (Optional)

To enable SMS delivery:

1. **Install Twilio:**
   ```bash
   pip install twilio
   ```

2. **Add to settings.py:**
   ```python
   TWILIO_ACCOUNT_SID = 'your-account-sid'
   TWILIO_AUTH_TOKEN = 'your-auth-token'
   TWILIO_PHONE_NUMBER = '+1234567890'
   ```

3. **Update views.py** (in forgot_password_method, around line 120):
   ```python
   from twilio.rest import Client
   
   client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
   message = client.messages.create(
       body=f'Your OTP is: {otp_obj.otp}',
       from_=settings.TWILIO_PHONE_NUMBER,
       to=profile.phone_number
   )
   ```

## 🧪 Quick Test Checklist

- [ ] Register user with email
- [ ] Click "Forgot Password?"
- [ ] Enter email
- [ ] Choose "Email" method
- [ ] Check `demodev/sent_emails/` for OTP
- [ ] Enter OTP on verification page
- [ ] Set new password
- [ ] Login with new password

## 📊 System Flow

```
User → Forgot Password Page
  ↓
Enter Email → Validate Email
  ↓
Choose Method (Email/SMS)
  ↓
Create OTP → Send Email
  ↓
Email saved to: demodev/sent_emails/
  ↓
User enters OTP → Verify OTP
  ↓
Set New Password → Update User
  ↓
Redirect to Login
  ↓
Login with New Password ✅
```

## 💡 Tips

1. **Keep sent_emails folder open** while testing for easy access to OTP codes
2. **Sort by date** to find the latest email quickly
3. **Copy OTP carefully** - must be exactly 6 digits
4. **Test within 10 minutes** - OTP expires after that
5. **Check browser console** for any error messages

## 🎯 Next Steps

After testing:
1. Configure production email (Gmail, SendGrid, etc.)
2. Add SMS integration (optional)
3. Add rate limiting to prevent brute force
4. Set up monitoring/logging
5. Deploy to production

---

**Status**: ✅ **WORKING AND READY TO USE**

The OTP system is fully functional. Emails are saved to `demodev/sent_emails/` for easy access during development.
