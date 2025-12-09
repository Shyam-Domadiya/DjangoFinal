# Real-Time OTP Setup - Quick Guide

## ⚡ 5-Minute Setup

### Option 1: Gmail Only (Recommended for Quick Start)

**Step 1:** Get Gmail App Password
- Go to: https://myaccount.google.com/apppasswords
- Enable 2FA first if not done
- Generate app password (16 characters)

**Step 2:** Update `demodev/demodev/settings.py`
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # 16-char app password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

**Step 3:** Restart Django and test!

---

### Option 2: SMS Only (Twilio)

**Step 1:** Install Twilio
```bash
pip install twilio
```

**Step 2:** Create Twilio Account
- Go to: https://www.twilio.com/
- Sign up and verify email
- Get Account SID and Auth Token
- Buy a phone number

**Step 3:** Update `demodev/demodev/settings.py`
```python
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN = 'your-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'
```

**Step 4:** Register user with phone number and test!

---

### Option 3: Both Gmail + SMS

Complete both Option 1 and Option 2 above.

Users will see both Email and SMS options when resetting password.

---

## 🧪 Quick Test

### Test Gmail
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test',
    'OTP: 123456',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False
)
print("Email sent!")
```

### Test Twilio
```bash
python manage.py shell
```

```python
from twilio.rest import Client
from django.conf import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
msg = client.messages.create(
    body='OTP: 123456',
    from_=settings.TWILIO_PHONE_NUMBER,
    to='+1234567890'  # Your phone
)
print(f"SMS sent! SID: {msg.sid}")
```

---

## 🚀 How It Works

### User Flow
1. Click "Forgot Password?"
2. Enter email
3. Choose method (Email or SMS)
4. Receive OTP in real-time
5. Enter OTP
6. Set new password
7. Login!

---

## 📋 Credentials You Need

### For Gmail
- Gmail address: `your-email@gmail.com`
- App password: `xxxx xxxx xxxx xxxx` (16 chars)

### For Twilio
- Account SID: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Auth Token: `your-auth-token`
- Phone Number: `+1234567890`

---

## ⚠️ Common Mistakes

1. **Using regular Gmail password instead of app password**
   - ❌ Wrong: `EMAIL_HOST_PASSWORD = 'mypassword123'`
   - ✅ Right: `EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'`

2. **Forgetting to enable 2FA on Gmail**
   - App passwords only work with 2FA enabled

3. **Wrong phone number format for Twilio**
   - ❌ Wrong: `to='1234567890'`
   - ✅ Right: `to='+1234567890'`

4. **Not installing Twilio SDK**
   - Run: `pip install twilio`

---

## 📞 Need Help?

See detailed guide: `.kiro/GMAIL_TWILIO_SETUP.md`

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Gmail credentials in settings.py
- [ ] Twilio credentials in settings.py (if using SMS)
- [ ] Twilio SDK installed (if using SMS)
- [ ] Test email sent successfully
- [ ] Test SMS sent successfully (if using SMS)
- [ ] Django restarted
- [ ] Can access `/forgot-password/`
- [ ] OTP received in real-time

---

**Status**: ✅ **READY TO SETUP**

Choose Gmail, Twilio, or both and follow the steps above!
