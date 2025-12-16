# Deploy Django Application on Render

## Step-by-Step Deployment Guide

### Prerequisites
- GitHub account
- Render account (https://render.com)
- Git installed locally

---

## Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)
```bash
cd DjangoFinal
git init
git add .
git commit -m "Initial commit: Django app with forgot password system"
```

### 1.2 Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your GitHub repositories

---

## Step 3: Create PostgreSQL Database on Render

1. **Go to Dashboard** → Click "New +"
2. **Select "PostgreSQL"**
3. **Configure Database**:
   - Name: `twitter-db`
   - Database: `twitter_db`
   - User: `twitter_user`
   - Region: Choose closest to you
   - Plan: Free (or paid if needed)
4. **Click "Create Database"**
5. **Copy the connection string** (you'll need it)

---

## Step 4: Create Web Service on Render

1. **Go to Dashboard** → Click "New +"
2. **Select "Web Service"**
3. **Connect Repository**:
   - Select your GitHub repository
   - Click "Connect"

4. **Configure Web Service**:
   - **Name**: `twitter-app` (or your preferred name)
   - **Environment**: Python 3
   - **Region**: Same as database
   - **Branch**: main
   - **Build Command**:
     ```
     pip install -r DjangoFinal/demodev/requirements.txt && python DjangoFinal/demodev/manage.py collectstatic --noinput && python DjangoFinal/demodev/manage.py migrate
     ```
   - **Start Command**:
     ```
     cd DjangoFinal/demodev && gunicorn demodev.wsgi:application
     ```
   - **Plan**: Free (or paid if needed)

5. **Add Environment Variables**:
   - Click "Add Environment Variable"
   - Add each variable below:

---

## Step 5: Set Environment Variables

Add these environment variables in Render dashboard:

### Required Variables
```
DEBUG=False
SECRET_KEY=<generate-a-random-secret-key>
PYTHONUNBUFFERED=1
```

### Database
```
DATABASE_URL=<paste-your-postgresql-connection-string>
```

### Allowed Hosts
```
ALLOWED_HOSTS=your-app-name.onrender.com,*.onrender.com,localhost,127.0.0.1
```

### Email Configuration (Gmail)
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Security
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## Step 6: Generate Secret Key

Generate a secure SECRET_KEY:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use an online generator: https://djecrety.ir/

---

## Step 7: Configure Gmail for Email

### 1. Enable 2-Factor Authentication
- Go to https://myaccount.google.com/security
- Enable 2-Step Verification

### 2. Generate App Password
- Go to https://myaccount.google.com/apppasswords
- Select "Mail" and "Windows Computer"
- Copy the generated password

### 3. Add to Render
- Set `EMAIL_HOST_USER` to your Gmail address
- Set `EMAIL_HOST_PASSWORD` to the app password

---

## Step 8: Deploy

1. **Click "Create Web Service"**
2. **Wait for deployment** (usually 5-10 minutes)
3. **Check deployment logs** for any errors
4. **Access your app** at `https://your-app-name.onrender.com`

---

## Step 9: Verify Deployment

### Check Application
1. Go to `https://your-app-name.onrender.com`
2. Test login functionality
3. Test forgot password system
4. Check email delivery

### Check Logs
1. Go to Render Dashboard
2. Select your web service
3. Click "Logs" tab
4. Review for any errors

---

## Troubleshooting

### Build Failed
**Solution**:
1. Check build logs for errors
2. Verify requirements.txt is correct
3. Check Python version compatibility
4. Ensure all dependencies are listed

### Application Not Starting
**Solution**:
1. Check start command is correct
2. Verify environment variables are set
3. Check database connection string
4. Review application logs

### Database Connection Error
**Solution**:
1. Verify DATABASE_URL is correct
2. Check database is running
3. Ensure migrations have run
4. Check database credentials

### Email Not Sending
**Solution**:
1. Verify EMAIL_HOST_USER is correct
2. Check EMAIL_HOST_PASSWORD is correct
3. Verify Gmail app password is generated
4. Check 2FA is enabled on Gmail
5. Review email logs

### Static Files Not Loading
**Solution**:
1. Run collectstatic command
2. Check STATIC_URL and STATIC_ROOT
3. Verify WhiteNoise is installed
4. Check build command includes collectstatic

---

## Post-Deployment

### 1. Create Superuser
```bash
# Via Render Shell
python manage.py createsuperuser
```

Or use Render's shell:
1. Go to Render Dashboard
2. Select your web service
3. Click "Shell" tab
4. Run: `python DjangoFinal/demodev/manage.py createsuperuser`

### 2. Access Admin Panel
```
https://your-app-name.onrender.com/secure-admin-panel-7x9k2m/
```

### 3. Test Forgot Password
```
https://your-app-name.onrender.com/forgot-password/
```

### 4. Monitor Application
- Check logs regularly
- Monitor email delivery
- Track user feedback
- Update as needed

---

## Useful Render Commands

### View Logs
```bash
# Via Render Dashboard → Logs tab
```

### Access Shell
```bash
# Via Render Dashboard → Shell tab
python manage.py shell
```

### Run Migrations
```bash
# Via Render Dashboard → Shell tab
python manage.py migrate
```

### Collect Static Files
```bash
# Via Render Dashboard → Shell tab
python manage.py collectstatic --noinput
```

---

## Environment Variables Reference

| Variable | Value | Required |
|----------|-------|----------|
| DEBUG | False | Yes |
| SECRET_KEY | Random string | Yes |
| DATABASE_URL | PostgreSQL connection | Yes |
| ALLOWED_HOSTS | your-domain.onrender.com | Yes |
| EMAIL_BACKEND | django.core.mail.backends.smtp.EmailBackend | Yes |
| EMAIL_HOST | smtp.gmail.com | Yes |
| EMAIL_PORT | 587 | Yes |
| EMAIL_USE_TLS | True | Yes |
| EMAIL_HOST_USER | your-email@gmail.com | Yes |
| EMAIL_HOST_PASSWORD | app-password | Yes |
| DEFAULT_FROM_EMAIL | your-email@gmail.com | Yes |
| SECURE_SSL_REDIRECT | True | Yes |
| SESSION_COOKIE_SECURE | True | Yes |
| CSRF_COOKIE_SECURE | True | Yes |
| PYTHONUNBUFFERED | 1 | Yes |

---

## Security Checklist

- [x] DEBUG = False
- [x] SECRET_KEY is random and secure
- [x] HTTPS enabled (SECURE_SSL_REDIRECT = True)
- [x] Secure cookies enabled
- [x] CSRF protection enabled
- [x] Email credentials are secure
- [x] Database credentials are secure
- [x] ALLOWED_HOSTS is configured
- [x] Static files are collected
- [x] Migrations are applied

---

## Performance Tips

1. **Use PostgreSQL** instead of SQLite
2. **Enable caching** for frequently accessed data
3. **Optimize database queries**
4. **Use CDN** for static files
5. **Monitor application performance**
6. **Set up error tracking** (Sentry)
7. **Monitor email delivery**

---

## Monitoring & Maintenance

### Daily
- Check application logs
- Monitor email delivery
- Check for errors

### Weekly
- Review user feedback
- Check performance metrics
- Update dependencies

### Monthly
- Review security logs
- Update Django and packages
- Backup database
- Review costs

---

## Scaling

### When to Scale
- High traffic (> 1000 requests/minute)
- Database performance issues
- Email delivery delays
- Static file serving issues

### Scaling Options
1. **Upgrade plan** (Free → Standard → Pro)
2. **Add more instances**
3. **Use CDN** for static files
4. **Optimize database** queries
5. **Implement caching**

---

## Rollback

If deployment fails:

1. **Go to Render Dashboard**
2. **Select your web service**
3. **Click "Deployments" tab**
4. **Select previous deployment**
5. **Click "Redeploy"**

---

## Support

### Render Support
- https://render.com/docs
- https://render.com/support

### Django Support
- https://docs.djangoproject.com/
- https://stackoverflow.com/questions/tagged/django

### Gmail Support
- https://support.google.com/mail

---

## Summary

Your Django application is now deployed on Render with:

✓ PostgreSQL database
✓ HTTPS enabled
✓ Email integration
✓ Forgot password system
✓ Admin panel
✓ REST API
✓ Static files serving
✓ Automatic deployments

**Status**: ✓ Ready for production

**Access**: https://your-app-name.onrender.com

**Admin**: https://your-app-name.onrender.com/secure-admin-panel-7x9k2m/

**Forgot Password**: https://your-app-name.onrender.com/forgot-password/

---

**Last Updated**: December 16, 2025
**Status**: ✓ Deployment Guide Complete
