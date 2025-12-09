# Real-Time OTP - Quick Start Card

## 🎯 Choose Your Setup

### Gmail (Email OTP) - 5 Minutes
```
1. Go to: https://myaccount.google.com/apppasswords
2. Generate 16-char app password
3. Update settings.py:
   EMAIL_HOST_USER = 'your-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'
   DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
4. Restart Django
5. Done! ✅
```

### Twilio (SMS OTP) - 10 Minutes
```
1. Create account: https://www.twilio.com/
2. Get Account SID, Auth Token, Phone Number
3. Install: pip install twilio
4. Update settings.py:
   TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
   TWILIO_AUTH_TOKEN = 'your-auth-token'
   TWILIO_PHONE_NUMBER = '+1234567890'
5. Restart Django
6. Done! ✅
```

### Both (Email + SMS) - 15 Minutes
```
Complete both Gmail and Twilio setup above
```

---

## 📍 Settings File Location
```
demodev/demodev/settings.py
```

---

## 🧪 Quick Test

### Test Gmail
```bash
python manage.py shell
```
```python
from django.core.mail import send_mail
from django.conf import settings
send_mail('Test', 'OTP: 123456', settings.DEFAULT_FROM_EMAIL, ['your-email@gmail.com'], fail_silently=False)
print("✅ Email sent!")
```

### Test Twilio
```bash
python manage.py shell
```
```python
from twilio.rest import Client
from django.conf import settings
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
msg = client.messages.create(body='OTP: 123456', from_=settings.TWILIO_PHONE_NUMBER, to='+1234567890')
print(f"✅ SMS sent! SID: {msg.sid}")
```

---

## 🚀 Test Password Reset

1. Go to: http://127.0.0.1:8000/register/
2. Create account with email/phone
3. Go to: http://127.0.0.1:8000/login/
4. Click "Forgot your password?"
5. Enter email
6. Choose method (Email or SMS)
7. Receive OTP in real-time ✅
8. Enter OTP
9. Set new password
10. Login ✅

---

## 📋 Credentials Format

### Gmail
```
Email: john@gmail.com
App Password: abcd efgh ijkl mnop
```

### Twilio
```
Account SID: ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p
Auth Token: abcdefghijklmnopqrstuvwxyz123456
Phone: +14155552671
```

---

## ⚠️ Common Mistakes

❌ Using regular Gmail password
✅ Use 16-char app password from Google

❌ Phone number: 1234567890
✅ Phone number: +1234567890

❌ Forgetting to enable 2FA on Gmail
✅ Enable 2FA first, then get app password

❌ Not installing Twilio
✅ Run: pip install twilio

---

## 📚 Full Guides

- **Gmail Setup**: `.kiro/STEP_BY_STEP_GMAIL_SETUP.md`
- **Twilio Setup**: `.kiro/STEP_BY_STEP_TWILIO_SETUP.md`
- **Quick Setup**: `.kiro/REAL_TIME_OTP_SETUP.md`
- **Complete Guide**: `.kiro/REAL_TIME_OTP_COMPLETE.md`

---

## ✅ Verification Checklist

- [ ] Credentials obtained
- [ ] settings.py updated
- [ ] Django restarted
- [ ] Test email/SMS sent successfully
- [ ] Password reset flow tested
- [ ] OTP received in real-time

---

## 🎯 Status

✅ **System Ready**
✅ **Code Updated**
✅ **Documentation Complete**

**Next Step**: Choose Gmail, Twilio, or both and follow the setup guide!

---

**Time to Setup**: 5-15 minutes
**Difficulty**: Easy
**Result**: Real-time OTP delivery ✅
