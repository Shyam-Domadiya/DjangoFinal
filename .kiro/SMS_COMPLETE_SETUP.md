# Complete SMS OTP Setup - Step by Step

## 📱 Send OTP via SMS to Mobile Number

---

## Step 1: Install Twilio SDK

Open terminal/command prompt and run:

```bash
pip install twilio
```

**Expected output:**
```
Successfully installed twilio-8.x.x
```

---

## Step 2: Create Twilio Account

### 2.1 Sign Up
1. Open: https://www.twilio.com/
2. Click **"Sign Up"** (top right)
3. Enter:
   - Email address
   - Password
   - Full name
4. Click **"Create Account"**

### 2.2 Verify Email
1. Check your email inbox
2. Click verification link
3. Complete signup process

### 2.3 Access Dashboard
1. Go to: https://console.twilio.com/
2. You're now on the Twilio dashboard

---

## Step 3: Get Your Credentials

### 3.1 Find Account SID and Auth Token

On the Twilio dashboard, you'll see:

```
Account SID: ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p
Auth Token: abcdefghijklmnopqrstuvwxyz123456
```

**Copy both values** and save them somewhere safe.

---

## Step 4: Buy a Twilio Phone Number

### 4.1 Navigate to Phone Numbers
1. In Twilio console, click **"Phone Numbers"** (left sidebar)
2. Click **"Manage"**
3. Click **"Buy a Number"**

### 4.2 Search for Number
1. Select your country (e.g., United States)
2. Click **"Search"**
3. You'll see available numbers

### 4.3 Purchase Number
1. Choose a number from the list
2. Click **"Buy"**
3. Confirm purchase
4. **Copy the phone number** (format: +1234567890)

**Example:**
```
+14155552671
```

---

## Step 5: Update Django Settings

Open: `demodev/demodev/settings.py`

Find this section (around line 145):
```python
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'  # Replace with your Twilio SID
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'  # Replace with your Twilio token
TWILIO_PHONE_NUMBER = '+1234567890'  # Replace with your Twilio phone number
```

Replace with your actual Twilio credentials:

**Example:**
```python
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = 'ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p'
TWILIO_AUTH_TOKEN = 'abcdefghijklmnopqrstuvwxyz123456'
TWILIO_PHONE_NUMBER = '+14155552671'
```

---

## Step 6: Restart Django

Stop the current Django server:
```
Press Ctrl+C
```

Restart Django:
```bash
python manage.py runserver
```

---

## Step 7: Test SMS Sending

### 7.1 Open Django Shell
```bash
python manage.py shell
```

### 7.2 Run Test Code
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

### 7.3 Expected Output
```
✅ SMS sent successfully!
Message SID: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 7.4 Check Your Phone
**You should receive an SMS with the OTP!**

---

## Step 8: Test Full Password Reset Flow

### 8.1 Register a User with Phone Number

1. Go to: http://127.0.0.1:8000/register/
2. Create account:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `TestPassword123`
   - Phone: `+1234567890` (your real phone number)
3. Click **"Register"**

### 8.2 Test Forgot Password

1. Go to: http://127.0.0.1:8000/login/
2. Click **"Forgot your password?"**
3. Enter email: `test@example.com`
4. Click **"Continue"**

### 8.3 Choose SMS Method

1. Select **"SMS"** option
2. Click **"Send OTP"**
3. You'll see: "OTP sent to +1234567890"

### 8.4 Receive OTP

**Check your phone** - you should receive SMS with OTP in seconds!

**SMS format:**
```
Your OTP is: 123456

This OTP will expire in 10 minutes.
```

### 8.5 Verify OTP

1. Copy the 6-digit OTP from SMS
2. Enter it on the verification page
3. Click **"Verify OTP"**
4. You'll see: "OTP verified successfully!"

### 8.6 Reset Password

1. Enter new password: `NewPassword456`
2. Confirm password: `NewPassword456`
3. Click **"Reset Password"**
4. You'll be redirected to login

### 8.7 Login with New Password

1. Username: `testuser`
2. Password: `NewPassword456`
3. Click **"Login"**
4. **Success!** ✅

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

## 📊 Settings.py Example

Here's what your settings should look like:

```python
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = 'ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p'
TWILIO_AUTH_TOKEN = 'abcdefghijklmnopqrstuvwxyz123456'
TWILIO_PHONE_NUMBER = '+14155552671'
```

---

## 💰 Twilio Pricing

- **Trial Account:** Free $15-20 credits
- **Production:** ~$0.0075 per SMS (varies by country)
- **Phone Number:** ~$1/month

**Estimate:** 100 OTP SMS = ~$0.75/month

---

## ✅ Verification Checklist

- [ ] Twilio SDK installed (`pip install twilio`)
- [ ] Twilio account created
- [ ] Account SID copied
- [ ] Auth Token copied
- [ ] Phone number purchased
- [ ] settings.py updated with credentials
- [ ] Django restarted
- [ ] Test SMS sent successfully from shell
- [ ] Test SMS received on phone
- [ ] User registered with phone number
- [ ] Password reset flow works with SMS
- [ ] OTP received on phone in real-time

---

## 🎯 Next Steps

After SMS is working:

1. **Test with multiple users**
   - Register different users with different phone numbers
   - Test password reset for each

2. **Monitor Twilio usage**
   - Go to: https://console.twilio.com/
   - Check "Logs" → "Messages"
   - See all SMS sent/received

3. **Optional: Add Gmail too**
   - Users can choose Email or SMS
   - See: `.kiro/FIX_GMAIL_CREDENTIALS.md`

4. **Deploy to production**
   - Use environment variables for credentials
   - Monitor SMS delivery

---

## 🔐 Security Notes

- Keep credentials safe - don't share them
- Never commit to Git
- Use environment variables in production
- Monitor for unusual activity
- Regenerate tokens if compromised

---

## 📞 Twilio Console

Monitor your SMS delivery:
1. Go to: https://console.twilio.com/
2. Click **"Logs"** → **"Messages"**
3. See all SMS sent/received
4. Check delivery status
5. View error messages

---

## ✨ Success Indicators

✅ **You'll know it's working when:**
1. Test SMS sent successfully in shell
2. SMS received on your phone
3. OTP appears in SMS
4. Password reset flow works
5. User receives OTP in real-time

---

**Status**: ✅ **READY TO SETUP SMS**

Follow the steps above and you'll have real-time SMS OTP delivery!
