# Fix Gmail Credentials Error

## ❌ Error You're Getting
```
Failed to send OTP: (535, b'5.7.8 Username and Password not accepted...
```

## ✅ Solution

The error means you're using **placeholder credentials** instead of your **real Gmail credentials**.

### Step 1: Get Your Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Make sure 2FA is enabled first
3. Select:
   - App: **Mail**
   - Device: **Windows Computer**
4. Click **Generate**
5. Google shows a 16-character password like:
   ```
   abcd efgh ijkl mnop
   ```
6. **Copy this exactly** (including spaces)

### Step 2: Update settings.py

Open: `demodev/demodev/settings.py`

Find this section (around line 130):
```python
EMAIL_HOST_USER = 'your-email@gmail.com'  # Replace with your Gmail address
EMAIL_HOST_PASSWORD = 'your-app-password'  # Replace with your Gmail app password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'  # Replace with your Gmail address
```

Replace with YOUR actual credentials:

**Example 1:**
```python
EMAIL_HOST_USER = 'john.doe@gmail.com'
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # Your 16-char app password
DEFAULT_FROM_EMAIL = 'john.doe@gmail.com'
```

**Example 2:**
```python
EMAIL_HOST_USER = 'myname@gmail.com'
EMAIL_HOST_PASSWORD = 'wxyz abcd efgh ijkl'  # Your 16-char app password
DEFAULT_FROM_EMAIL = 'myname@gmail.com'
```

### Step 3: Restart Django

Stop Django (Ctrl+C) and restart:
```bash
python manage.py runserver
```

### Step 4: Test Again

Go to `/forgot-password/` and try sending OTP again.

---

## ⚠️ Important Notes

1. **Use app password, NOT your regular Gmail password**
   - ❌ Wrong: `EMAIL_HOST_PASSWORD = 'mypassword123'`
   - ✅ Right: `EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'`

2. **Include spaces in the app password**
   - ❌ Wrong: `abcdefghijklmnop`
   - ✅ Right: `abcd efgh ijkl mnop`

3. **Make sure 2FA is enabled**
   - App passwords only work with 2FA enabled
   - Enable at: https://myaccount.google.com/security

4. **Email address must match**
   - `EMAIL_HOST_USER` should be your Gmail address
   - `DEFAULT_FROM_EMAIL` should be the same

---

## 🧪 Test After Fixing

### Test in Django Shell
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test OTP',
    'Your OTP is: 123456',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False
)
print("✅ Email sent successfully!")
```

If you see "✅ Email sent successfully!" and receive an email, you're good!

### Test Password Reset
1. Go to: http://127.0.0.1:8000/forgot-password/
2. Enter your email
3. Choose "Email" method
4. Click "Send OTP"
5. Check your Gmail inbox for the OTP ✅

---

## 🔍 Troubleshooting

### Still Getting "Username and Password not accepted"?

**Check:**
1. ✅ 2FA is enabled on your Gmail account
2. ✅ You're using the 16-char app password (not regular password)
3. ✅ App password includes spaces exactly as shown by Google
4. ✅ Email address is correct
5. ✅ Django has been restarted

### If Still Not Working

1. Generate a **new app password**
   - Go to: https://myaccount.google.com/apppasswords
   - Delete old password
   - Generate new one
   - Copy exactly

2. Update settings.py with the new password

3. Restart Django

4. Try again

---

## 📋 Checklist

- [ ] 2FA enabled on Gmail
- [ ] App password generated (16 characters)
- [ ] App password copied exactly (with spaces)
- [ ] settings.py updated with correct email
- [ ] settings.py updated with correct app password
- [ ] Django restarted
- [ ] Test email sent successfully
- [ ] Test email received in Gmail inbox

---

## ✅ You're Done!

Once you see "✅ Email sent successfully!" in the shell, your Gmail is configured correctly and OTP will work!

---

**Status**: Ready to fix! Follow the steps above.
