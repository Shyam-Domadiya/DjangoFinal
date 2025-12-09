# Gmail OTP Troubleshooting Guide

## Error: "Username and Password not accepted"

This is the most common error. Here's how to fix it.

---

## 🔍 Root Causes

### Cause 1: Using Regular Password Instead of App Password
**Problem:** You're using your Gmail login password
**Solution:** Use the 16-character app password from Google

### Cause 2: 2FA Not Enabled
**Problem:** App passwords only work with 2FA enabled
**Solution:** Enable 2FA first

### Cause 3: Wrong Email Address
**Problem:** EMAIL_HOST_USER doesn't match your Gmail
**Solution:** Use your actual Gmail address

### Cause 4: Spaces Missing in App Password
**Problem:** App password copied without spaces
**Solution:** Include spaces exactly as shown by Google

### Cause 5: Django Not Restarted
**Problem:** Old settings still in memory
**Solution:** Restart Django after updating settings

---

## ✅ Step-by-Step Fix

### Step 1: Verify 2FA is Enabled

1. Go to: https://myaccount.google.com/security
2. Look for **"2-Step Verification"**
3. If it says **"Off"**, click it and enable it
4. If it says **"On"**, you're good ✅

### Step 2: Generate New App Password

1. Go to: https://myaccount.google.com/apppasswords
2. You should see a dropdown menu
3. Select:
   - **App:** Mail
   - **Device:** Windows Computer (or your device)
4. Click **"Generate"**
5. Google shows a 16-character password:
   ```
   abcd efgh ijkl mnop
   ```
6. **Copy this exactly** (with spaces)

### Step 3: Update settings.py

Open: `demodev/demodev/settings.py`

Find (around line 130):
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

Replace with your actual values:
```python
EMAIL_HOST_USER = 'john.doe@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # Your 16-char app password (with spaces!)
DEFAULT_FROM_EMAIL = 'john.doe@gmail.com'  # Same as EMAIL_HOST_USER
```

### Step 4: Restart Django

Stop Django:
```
Press Ctrl+C
```

Restart Django:
```bash
python manage.py runserver
```

### Step 5: Test

Open Django shell:
```bash
python manage.py shell
```

Run:
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
print("✅ Success!")
```

**Expected output:**
```
✅ Success!
```

**Check your Gmail inbox** - you should receive the test email!

---

## 🎯 Common Mistakes

### ❌ Mistake 1: Using Regular Password
```python
# WRONG!
EMAIL_HOST_PASSWORD = 'mypassword123'
```

### ✅ Correct: Using App Password
```python
# RIGHT!
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'
```

---

### ❌ Mistake 2: Removing Spaces
```python
# WRONG!
EMAIL_HOST_PASSWORD = 'abcdefghijklmnop'
```

### ✅ Correct: Keeping Spaces
```python
# RIGHT!
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'
```

---

### ❌ Mistake 3: Wrong Email
```python
# WRONG!
EMAIL_HOST_USER = 'your-email@gmail.com'  # Placeholder!
```

### ✅ Correct: Your Real Email
```python
# RIGHT!
EMAIL_HOST_USER = 'john.doe@gmail.com'  # Your actual Gmail
```

---

## 🧪 Verification Checklist

- [ ] 2FA enabled on Gmail account
- [ ] App password generated (16 characters)
- [ ] App password copied with spaces
- [ ] EMAIL_HOST_USER = your Gmail address
- [ ] EMAIL_HOST_PASSWORD = 16-char app password
- [ ] DEFAULT_FROM_EMAIL = your Gmail address
- [ ] Django restarted
- [ ] Test email sent successfully
- [ ] Test email received in Gmail inbox

---

## 📊 Settings.py Example

Here's what your settings should look like:

```python
# Email Configuration for Password Reset OTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'john.doe@gmail.com'  # ← Your Gmail address
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # ← Your 16-char app password
DEFAULT_FROM_EMAIL = 'john.doe@gmail.com'  # ← Same as EMAIL_HOST_USER
```

---

## 🔐 Security Notes

- **Never use your regular Gmail password**
- **App passwords are specific to your account**
- **Keep app password safe - don't share it**
- **Never commit to Git**
- **Use environment variables in production**

---

## 📞 Still Not Working?

### Try These Steps

1. **Generate a new app password**
   - Delete old one
   - Generate new one
   - Copy exactly

2. **Double-check email address**
   - Make sure it matches your Gmail

3. **Verify 2FA is ON**
   - Go to: https://myaccount.google.com/security

4. **Restart Django completely**
   - Stop (Ctrl+C)
   - Wait 2 seconds
   - Start again

5. **Test in Django shell**
   - Run the test code above
   - Check for error messages

---

## 🎓 Understanding App Passwords

**What is an app password?**
- A 16-character password specific to your Gmail account
- Only works with 2FA enabled
- More secure than your regular password
- Can be revoked anytime

**Why use app password?**
- More secure than regular password
- Can be revoked without changing main password
- Specific to this application
- Google recommends it

**How to revoke?**
- Go to: https://myaccount.google.com/apppasswords
- Click the app password
- Click "Remove"
- Generate a new one if needed

---

## ✨ Success Indicators

✅ **You'll know it's working when:**
1. Test email sent successfully in shell
2. Email received in Gmail inbox
3. OTP appears in email
4. Password reset flow works
5. User receives OTP in real-time

---

## 🚀 Next Steps

Once Gmail is working:
1. Test the full password reset flow
2. Register a test user
3. Try forgot password
4. Verify OTP is received
5. Complete password reset
6. Login with new password ✅

---

**Status**: Follow the steps above to fix the Gmail credentials error!
