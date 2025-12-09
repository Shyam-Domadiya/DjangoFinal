# Send OTP to User's Phone Number

## ✅ How It Works

When a user registers with their phone number and requests password reset:

1. User registers with phone number: `+1234567890`
2. User clicks "Forgot Password?"
3. User chooses "SMS" method
4. **OTP is sent to their phone number** `+1234567890` ✅

---

## 🚀 Setup Steps

### Step 1: Install Twilio
```bash
pip install twilio
```

### Step 2: Create Twilio Account
- Go to: https://www.twilio.com/
- Sign up
- Get Account SID, Auth Token, and buy phone number

### Step 3: Update settings.py
```python
TWILIO_ACCOUNT_SID = 'ACa1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p'
TWILIO_AUTH_TOKEN = 'abcdefghijklmnopqrstuvwxyz123456'
TWILIO_PHONE_NUMBER = '+14155552671'  # Twilio phone number
```

### Step 4: Restart Django
```bash
python manage.py runserver
```

---

## 📱 User Flow

### Step 1: Register with Phone Number
```
Go to: http://127.0.0.1:8000/register/

Username: john
Email: john@example.com
Password: Password123
Phone: +1234567890  ← User's own phone number
```

### Step 2: Forgot Password
```
Go to: http://127.0.0.1:8000/login/
Click: "Forgot your password?"
Enter: john@example.com
Click: "Continue"
```

### Step 3: Choose SMS Method
```
Select: SMS
Click: "Send OTP"
```

### Step 4: Receive OTP
**User receives SMS on their phone:**
```
Your OTP is: 123456

This OTP will expire in 10 minutes.
```

### Step 5: Verify OTP
```
Enter: 123456
Click: "Verify OTP"
```

### Step 6: Reset Password
```
Enter new password
Confirm password
Click: "Reset Password"
```

### Step 7: Login
```
Username: john
Password: NewPassword123
Click: "Login"
```

---

## 🔄 How the Code Works

### Registration
```python
# User registers with phone number
UserProfile.objects.create(
    user=user,
    phone_number='+1234567890'  # Stored in database
)
```

### Password Reset
```python
# When user requests SMS OTP
profile = user.profile
phone_number = profile.phone_number  # Get user's phone number

# Send OTP to user's phone
client.messages.create(
    body=f'Your OTP is: {otp_obj.otp}',
    from_=settings.TWILIO_PHONE_NUMBER,  # Twilio phone
    to=profile.phone_number  # User's phone ✅
)
```

---

## ✅ Verification

### Check User Profile
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from tweet.models import UserProfile

user = User.objects.get(username='john')
profile = user.profile
print(f"User: {user.username}")
print(f"Phone: {profile.phone_number}")
```

**Output:**
```
User: john
Phone: +1234567890
```

---

## 📋 Checklist

- [ ] Twilio SDK installed
- [ ] Twilio account created
- [ ] Twilio credentials in settings.py
- [ ] Django restarted
- [ ] User registered with phone number
- [ ] User can see phone number in profile
- [ ] Password reset sends OTP to user's phone
- [ ] User receives OTP in seconds

---

## 🎯 Summary

✅ **System automatically sends OTP to user's phone number**

1. User registers with phone number
2. Phone number stored in UserProfile
3. When user requests SMS OTP, it's sent to their phone
4. User receives OTP in real-time
5. User verifies OTP and resets password

**No additional setup needed!** Just configure Twilio credentials and it works automatically.

---

**Status**: ✅ **READY TO USE**

Follow the setup steps and OTP will be sent to each user's own phone number!
