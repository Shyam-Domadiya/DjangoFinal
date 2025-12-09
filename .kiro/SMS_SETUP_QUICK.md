# SMS OTP Setup - Quick Guide

## 📱 Send OTP via SMS to Mobile Number

### Step 1: Install Twilio SDK

```bash
pip install twilio
```

### Step 2: Create Twilio Account

1. Go to: https://www.twilio.com/
2. Click **"Sign Up"**
3. Create account with email and password
4. Verify your email
5. Complete signup

### Step 3: Get Twilio Credentials

1. Go to: https://console.twilio.com/
2. On dashboard, you'll see:
   - **Account SID** (starts with AC...)
   - **Auth Token** (long string)
3. **Copy both values**

### Step 4: Buy Twilio Phone Number

1. In Twilio console, click **"Phone Numbers"**
2. Click **"Manage"** → **"Buy a Number"**
3. Select your country
4. Click **"Search"**
5. Choose a number
6. Click **"Buy"**
7. **Copy the phone number** (format: +1234567890)

### Step 5: Update settings.py

Open: `demodev/demodev/settings.py`

Find (around line 145):
```python
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'
```

Replace with your actual Twilio credentials:
```python
TWILIO_ACCOUNT_SID = 'ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p'
TWILIO_AUTH_TOKEN = 'abcdefghijklmnopqrstuvwxyz123456'
TWILIO_PHONE_NUMBER = '+14155552671'
```

### Step 6: Restart Django

Stop Django (Ctrl+C) and restart:
```bash
python manage.py runserver
```

### Step 7: Test SMS

Open Django shell:
```bash
python manage.py shell
```

Run:
```python
from twilio.rest import Client
from django.conf import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
msg = client.messages.create(
    body='Your OTP is: 123456',
    from_=settings.TWILIO_PHONE_NUMBER,
    to='+1234567890'  # Your phone number
)
print(f"✅ SMS sent! SID: {msg.sid}")
```

**Check your phone** - you should receive the SMS!

### Step 8: Test Password Reset with SMS

1. Go to: http://127.0.0.1:8000/register/
2. Create account with:
   - Email: `test@example.com`
   - Phone: `+1234567890` (your real phone)
3. Go to: http://127.0.0.1:8000/login/
4. Click **"Forgot your password?"**
5. Enter email
6. Select **"SMS"** method
7. Click **"Send OTP"**
8. **Check your phone** - OTP arrives in seconds! ✅
9. Enter OTP
10. Set new password
11. Login ✅

---

## 📋 Credentials Format

### Twilio Credentials
```
Account SID: ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p
Auth Token: abcdefghijklmnopqrstuvwxyz123456
Phone Number: +14155552671
```

---

## ⚠️ Important Notes

1. **Phone number format**: Must be +1234567890 (with country code)
2. **Install Twilio**: `pip install twilio`
3. **Restart Django** after updating settings
4. **User must have phone number** in profile to use SMS
5. **Twilio has free trial** with $15-20 credits

---

## 🧪 Verification Checklist

- [ ] Twilio SDK installed
- [ ] Twilio account created
- [ ] Account SID copied
- [ ] Auth Token copied
- [ ] Phone number purchased
- [ ] settings.py updated with credentials
- [ ] Django restarted
- [ ] Test SMS sent successfully
- [ ] Test SMS received on phone

---

## 💰 Twilio Pricing

- **Trial**: Free $15-20 credits
- **Production**: ~$0.0075 per SMS
- **Phone Number**: ~$1/month

---

## ✅ You're Done!

Once SMS test works, users can:
1. Register with phone number
2. Use "SMS" option in password reset
3. Receive OTP on their phone in real-time ✅

---

**Status**: Ready to setup SMS!
