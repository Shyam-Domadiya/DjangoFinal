# Real-Time OTP Setup - Gmail & Twilio

## 📧 Gmail Setup (Email OTP)

### Step 1: Enable 2-Factor Authentication on Gmail

1. Go to: https://myaccount.google.com/
2. Click **"Security"** in the left menu
3. Scroll down to **"2-Step Verification"**
4. Click **"Get Started"**
5. Follow the prompts to enable 2FA

### Step 2: Create App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select **"Mail"** and **"Windows Computer"** (or your device)
3. Click **"Generate"**
4. Google will show a 16-character password
5. **Copy this password** (you'll need it)

### Step 3: Update Django Settings

Edit `demodev/demodev/settings.py`:

```python
# Email Configuration for Password Reset OTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # 16-char app password (with spaces)
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'  # Your Gmail address
```

**Example:**
```python
EMAIL_HOST_USER = 'myname@gmail.com'
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # App password from Google
DEFAULT_FROM_EMAIL = 'myname@gmail.com'
```

### Step 4: Test Gmail Configuration

Run this command in Django shell:

```bash
python manage.py shell
```

Then in the shell:

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test OTP: 123456',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False
)
print("Email sent successfully!")
```

If successful, you'll receive an email in your Gmail inbox!

---

## 📱 Twilio Setup (SMS OTP)

### Step 1: Create Twilio Account

1. Go to: https://www.twilio.com/
2. Click **"Sign Up"**
3. Create account with your email and password
4. Verify your email
5. Complete the signup process

### Step 2: Get Twilio Credentials

1. Go to: https://console.twilio.com/
2. On the dashboard, you'll see:
   - **Account SID** (starts with AC...)
   - **Auth Token** (long string)
3. **Copy both values**

### Step 3: Get Twilio Phone Number

1. In Twilio console, click **"Phone Numbers"** → **"Manage"**
2. Click **"Buy a Number"**
3. Select your country and click **"Search"**
4. Choose a number and click **"Buy"**
5. **Copy the phone number** (format: +1234567890)

### Step 4: Install Twilio SDK

```bash
pip install twilio
```

### Step 5: Update Django Settings

Edit `demodev/demodev/settings.py`:

```python
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  # Your Account SID
TWILIO_AUTH_TOKEN = 'your-auth-token-here'  # Your Auth Token
TWILIO_PHONE_NUMBER = '+1234567890'  # Your Twilio phone number
```

**Example:**
```python
TWILIO_ACCOUNT_SID = 'ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p'
TWILIO_AUTH_TOKEN = 'abcdefghijklmnopqrstuvwxyz123456'
TWILIO_PHONE_NUMBER = '+14155552671'
```

### Step 6: Test Twilio Configuration

Run this command in Django shell:

```bash
python manage.py shell
```

Then in the shell:

```python
from twilio.rest import Client
from django.conf import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
message = client.messages.create(
    body='Test OTP: 123456',
    from_=settings.TWILIO_PHONE_NUMBER,
    to='+1234567890'  # Your phone number
)
print(f"SMS sent! Message SID: {message.sid}")
```

If successful, you'll receive an SMS on your phone!

---

## 🚀 How to Use

### Email OTP (Gmail)

1. Go to `/forgot-password/`
2. Enter your email
3. Click **"Continue"**
4. Select **"Email"** method
5. Click **"Send OTP"**
6. Check your Gmail inbox for the OTP
7. Enter OTP on verification page
8. Set new password

### SMS OTP (Twilio)

1. Go to `/forgot-password/`
2. Enter your email
3. Click **"Continue"**
4. Select **"SMS"** method (only shows if phone number is on file)
5. Click **"Send OTP"**
6. Check your phone for the SMS
7. Enter OTP on verification page
8. Set new password

---

## 🔧 Troubleshooting

### Gmail Issues

**Problem:** "SMTPAuthenticationError: 535 5.7.8 Username and password not accepted"

**Solutions:**
1. Make sure 2FA is enabled on your Gmail account
2. Use the 16-character app password (not your regular password)
3. Include spaces in the app password as shown by Google
4. Check that EMAIL_HOST_USER matches your Gmail address

**Problem:** "SMTPNotSupportedError: SMTP AUTH extension not supported by server"

**Solution:**
- Make sure `EMAIL_USE_TLS = True` in settings

### Twilio Issues

**Problem:** "twilio.base.exceptions.TwilioRestException: [HTTP 401] Unauthorized"

**Solutions:**
1. Check that TWILIO_ACCOUNT_SID is correct
2. Check that TWILIO_AUTH_TOKEN is correct
3. Make sure you copied them exactly (no extra spaces)

**Problem:** "twilio.base.exceptions.TwilioRestException: [HTTP 400] Invalid 'To' Phone Number"

**Solutions:**
1. Phone number must be in format: +1234567890
2. Must include country code (+1 for USA)
3. Check that user's phone number is in correct format

**Problem:** "Twilio module not found"

**Solution:**
```bash
pip install twilio
```

---

## 📋 Configuration Checklist

### Gmail Setup
- [ ] 2FA enabled on Gmail account
- [ ] App password generated
- [ ] EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
- [ ] EMAIL_HOST = 'smtp.gmail.com'
- [ ] EMAIL_PORT = 587
- [ ] EMAIL_USE_TLS = True
- [ ] EMAIL_HOST_USER = your Gmail address
- [ ] EMAIL_HOST_PASSWORD = 16-char app password
- [ ] DEFAULT_FROM_EMAIL = your Gmail address
- [ ] Test email sent successfully

### Twilio Setup
- [ ] Twilio account created
- [ ] Account SID copied
- [ ] Auth Token copied
- [ ] Twilio phone number purchased
- [ ] Twilio SDK installed (pip install twilio)
- [ ] TWILIO_ACCOUNT_SID configured
- [ ] TWILIO_AUTH_TOKEN configured
- [ ] TWILIO_PHONE_NUMBER configured
- [ ] Test SMS sent successfully

---

## 🎯 Quick Start

### For Gmail Only (Email OTP)

1. Get Gmail app password
2. Update settings.py with Gmail credentials
3. Restart Django
4. Test at `/forgot-password/`

### For SMS Only (Twilio)

1. Create Twilio account
2. Get credentials and phone number
3. Install Twilio: `pip install twilio`
4. Update settings.py with Twilio credentials
5. Register user with phone number
6. Restart Django
7. Test at `/forgot-password/`

### For Both (Email + SMS)

1. Complete Gmail setup
2. Complete Twilio setup
3. Restart Django
4. Users can choose Email or SMS method

---

## 📧 Gmail App Password Example

When you generate an app password in Google, you'll see:

```
Your app password for your Google Account is:

abcd efgh ijkl mnop
```

Use exactly as shown (with spaces):
```python
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'
```

---

## 🔐 Security Notes

- Never commit credentials to Git
- Use environment variables for production
- Keep app passwords secure
- Regenerate if compromised
- Use strong passwords

---

## 📞 Support

For issues:
1. Check the troubleshooting section above
2. Verify all credentials are correct
3. Test in Django shell first
4. Check Django error messages
5. Review Gmail/Twilio documentation

---

## ✨ What's Next

After setup:
1. Test both email and SMS
2. Add rate limiting to prevent abuse
3. Add logging for security
4. Monitor OTP delivery
5. Set up alerts for failures

---

**Status**: ✅ **READY FOR REAL-TIME OTP DELIVERY**

Follow the steps above to enable Gmail and/or Twilio for real-time OTP delivery!
