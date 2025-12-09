# Step-by-Step Twilio SMS Setup for Real-Time OTP

## Complete Guide with Examples

### Step 1: Create Twilio Account

1. Open: https://www.twilio.com/
2. Click **"Sign Up"** (top right)
3. Enter:
   - Email address
   - Password
   - Full name
4. Click **"Create Account"**
5. Verify your email
6. Complete signup process

### Step 2: Get Twilio Credentials

1. Go to: https://console.twilio.com/
2. On the dashboard, you'll see:
   - **Account SID** (starts with AC...)
   - **Auth Token** (long string)

**Example:**
```
Account SID: ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p
Auth Token: abcdefghijklmnopqrstuvwxyz123456
```

3. **Copy both values** and save them

### Step 3: Buy a Twilio Phone Number

1. In Twilio console, click **"Phone Numbers"**
2. Click **"Manage"** → **"Buy a Number"**
3. Select your country (e.g., United States)
4. Click **"Search"**
5. Choose a number from the list
6. Click **"Buy"** and confirm
7. **Copy the phone number** (format: +1234567890)

**Example:**
```
+14155552671
```

### Step 4: Install Twilio SDK

Open terminal/command prompt and run:
```bash
pip install twilio
```

**Expected output:**
```
Successfully installed twilio-8.x.x
```

### Step 5: Update Django Settings

Open: `demodev/demodev/settings.py`

Find this section:
```python
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'
```

Replace with your actual values:

**Example:**
```python
TWILIO_ACCOUNT_SID = 'ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p'
TWILIO_AUTH_TOKEN = 'abcdefghijklmnopqrstuvwxyz123456'
TWILIO_PHONE_NUMBER = '+14155552671'
```

### Step 6: Restart Django

Stop the current Django server (Ctrl+C) and restart:
```bash
python manage.py runserver
```

### Step 7: Test SMS Sending

Open Django shell:
```bash
python manage.py shell
```

Run this code:
```python
from twilio.rest import Client
from django.conf import settings

# Create Twilio client
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# Send test SMS
message = client.messages.create(
    body='Your OTP is: 123456\n\nThis OTP will expire in 10 minutes.',
    from_=settings.TWILIO_PHONE_NUMBER,
    to='+1234567890'  # Replace with your phone number
)

print(f"✅ SMS sent successfully!")
print(f"Message SID: {message.sid}")
```

**Expected output:**
```
✅ SMS sent successfully!
Message SID: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Check your phone** - you should receive the test SMS!

### Step 8: Test Password Reset Flow with SMS

1. Go to: http://127.0.0.1:8000/register/
2. Create a test account:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `TestPassword123`
   - Phone: `+1234567890` (your real phone number)

3. Go to: http://127.0.0.1:8000/login/
4. Click **"Forgot your password?"**
5. Enter your email: `test@example.com`
6. Click **"Continue"**
7. Select **"SMS"** method
8. Click **"Send OTP"**
9. **Check your phone** - OTP should arrive in seconds!
10. Copy the OTP from the SMS
11. Enter OTP on the verification page
12. Set new password
13. Login with new password ✅

---

## 🔍 Troubleshooting

### Error: "twilio.base.exceptions.TwilioRestException: [HTTP 401] Unauthorized"

**Cause:** Wrong Account SID or Auth Token

**Fix:**
1. Go to: https://console.twilio.com/
2. Copy Account SID and Auth Token again
3. Make sure no extra spaces
4. Update settings.py
5. Restart Django

### Error: "twilio.base.exceptions.TwilioRestException: [HTTP 400] Invalid 'To' Phone Number"

**Cause:** Wrong phone number format

**Fix:**
- ❌ Wrong: `to='1234567890'`
- ✅ Right: `to='+1234567890'`
- Must include country code (+1 for USA)

### Error: "ModuleNotFoundError: No module named 'twilio'"

**Cause:** Twilio SDK not installed

**Fix:**
```bash
pip install twilio
```

### SMS not arriving

**Cause:** Multiple possible reasons

**Fix:**
1. Check phone number format (+1234567890)
2. Check Twilio account has credits
3. Check phone number is correct
4. Try sending again
5. Check Twilio console for delivery status

### "SMS option not showing" in password reset

**Cause:** User doesn't have phone number in profile

**Fix:**
1. Register user with phone number
2. Or update user profile with phone number
3. Try password reset again

---

## 💰 Twilio Pricing

- **Trial Account:** Free credits ($15-$20)
- **Production:** ~$0.0075 per SMS (varies by country)
- **Phone Number:** ~$1/month

**Estimate:** 100 OTP SMS = ~$0.75/month

---

## ✅ Verification Steps

After setup, verify each step:

- [ ] Twilio account created
- [ ] Account SID copied
- [ ] Auth Token copied
- [ ] Phone number purchased
- [ ] Twilio SDK installed
- [ ] settings.py updated with credentials
- [ ] Django restarted
- [ ] Test SMS sent successfully from shell
- [ ] Test SMS received on phone
- [ ] Password reset flow works with SMS

---

## 📱 SMS Format

When user requests OTP via SMS, they'll receive:

```
Your OTP is: 123456

This OTP will expire in 10 minutes.
```

---

## 🎯 Next Steps

After Twilio is working:

1. **Optional:** Set up Gmail for email OTP
   - See: `.kiro/STEP_BY_STEP_GMAIL_SETUP.md`

2. **Optional:** Add rate limiting
   - Prevent brute force attacks

3. **Optional:** Add logging
   - Track SMS delivery

4. **Deploy:** Move to production
   - Use environment variables for credentials

---

## 💡 Tips

1. **Keep credentials safe** - don't share them
2. **Monitor Twilio usage** - watch for abuse
3. **Use environment variables** in production
4. **Test before deploying** to production
5. **Set up alerts** for failed deliveries

---

## 🔐 Security Notes

- Credentials are sensitive - keep them safe
- Never commit to Git
- Use environment variables in production
- Monitor for unusual activity
- Regenerate tokens if compromised

---

## 📊 Twilio Console

Monitor your SMS delivery:
1. Go to: https://console.twilio.com/
2. Click **"Logs"** → **"Messages"**
3. See all SMS sent/received
4. Check delivery status
5. View error messages

---

**Status**: ✅ **READY TO SETUP**

Follow the steps above and you'll have real-time SMS OTP delivery!
