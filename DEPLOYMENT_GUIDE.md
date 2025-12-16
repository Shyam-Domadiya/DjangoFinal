# Django Render Deployment Guide

## Overview
This guide explains the production deployment configuration for the Django Tweet Application on Render.

---

## Part 1: Issues Fixed

### 1. Port Binding Issue ✓ FIXED
**Problem:** Gunicorn was binding to `127.0.0.1:8000` (localhost only), making it invisible to Render's health checks.

**Solution:**
```bash
# Before (incorrect)
gunicorn --chdir demodev demodev.wsgi:application

# After (correct)
gunicorn --chdir demodev --bind 0.0.0.0:$PORT --workers 3 --timeout 60 --access-logfile - --error-logfile - demodev.wsgi:application
```

**Why it works:**
- `0.0.0.0:$PORT` binds to all interfaces on Render's assigned port
- Render can now detect the service is listening
- Health checks will succeed

### 2. Static Files Issue ✓ FIXED
**Problem:** `STATICFILES_DIRS` pointed to non-existent directory, causing 0-byte responses.

**Solution:**
```python
# Before (incorrect)
STATICFILES_DIRS = [os.path.join(BASE_DIR,'static')]

# After (correct)
static_dir = os.path.join(BASE_DIR, 'static')
if os.path.exists(static_dir):
    STATICFILES_DIRS = [static_dir]
else:
    STATICFILES_DIRS = []
```

**Why it works:**
- Only includes directory if it exists
- WhiteNoise handles missing directories gracefully
- Static files are collected during build phase

### 3. Logging Issues ✓ FIXED
**Problem:** No access logs, health checks create noise, hard to debug errors.

**Solution:**
- Added structured logging with timestamps and function names
- Separate handlers for access logs, errors, and debug logs
- Filter to skip health check noise
- Gunicorn logs to stdout/stderr

**Benefits:**
- Clear separation of concerns
- Easy to grep for errors
- Can see request patterns
- Health checks don't clutter logs

### 4. HTTPS Configuration ✓ FIXED
**Problem:** `SECURE_PROXY_SSL_HEADER` not set in environment variables.

**Solution:**
```yaml
- key: SECURE_PROXY_SSL_HEADER
  value: "HTTP_X_FORWARDED_PROTO,https"
```

**Why it works:**
- Tells Django to trust Render's proxy headers
- Correctly detects HTTPS requests
- Prevents redirect loops

---

## Part 2: Files Modified

### 1. `render.yaml`
**Changes:**
- Updated `startCommand` with proper port binding and logging
- Added `SECURE_PROXY_SSL_HEADER` environment variable
- Simplified paths (removed `DjangoFinal/` prefix)

### 2. `Procfile`
**Changes:**
- Updated web process with proper port binding
- Simplified paths for consistency
- Added logging flags

### 3. `demodev/demodev/settings.py`
**Changes:**
- Fixed `STATICFILES_DIRS` to check if directory exists
- Improved logging configuration with structured output
- Added filters to skip health check noise
- Added separate handlers for different log levels

### 4. `demodev/gunicorn_config.py` (NEW)
**Purpose:**
- Centralized Gunicorn configuration
- Easy to adjust workers, timeouts, logging
- Server hooks for debugging

---

## Part 3: How to Read Render Logs

### Access Logs
```
[INFO] 2025-12-16 10:30:45 gunicorn.access - 127.0.0.1 - - "GET /tweets/ HTTP/1.1" 200 5234 "-" "Mozilla/5.0" 45000
```
- Shows all HTTP requests
- Status codes (200, 404, 500, etc.)
- Response time in microseconds (last number)

### Error Logs
```
[ERROR] 2025-12-16 10:31:12 django.request handle - Internal Server Error: /api/tweets/
Traceback (most recent call last):
  File "...", line 123, in get_tweets
    ...
```
- Shows actual errors with stack traces
- Easy to identify problems
- Includes file and line numbers

### Startup Logs
```
[GUNICORN] Starting server...
[GUNICORN] Server is ready. Spawning workers on 0.0.0.0:10000
```
- Confirms server started correctly
- Shows port binding
- Useful for deployment verification

### Health Check Logs (FILTERED OUT)
```
# These are now filtered and won't appear
GET /health HTTP/1.1 200
```

---

## Part 4: Deployment Checklist

### Before Deploying
- [ ] All environment variables set in Render dashboard
- [ ] Database URL configured
- [ ] Email credentials set (if using forgot password)
- [ ] SECRET_KEY generated

### During Deployment
- [ ] Build completes without errors
- [ ] Migrations run successfully
- [ ] Static files collected
- [ ] Server starts on correct port

### After Deployment
- [ ] Check Render logs for startup messages
- [ ] Test main endpoints (register, login, tweets)
- [ ] Verify static files load (CSS, JS)
- [ ] Test forgot password (if email configured)
- [ ] Monitor logs for errors

---

## Part 5: Troubleshooting

### "No open ports detected"
**Cause:** Gunicorn not binding to `0.0.0.0:$PORT`
**Fix:** Check `startCommand` in render.yaml includes `--bind 0.0.0.0:$PORT`

### Static files return 0 bytes
**Cause:** `STATICFILES_DIRS` points to non-existent directory
**Fix:** Run `python manage.py collectstatic` locally to verify

### HTTPS redirect loop
**Cause:** `SECURE_PROXY_SSL_HEADER` not set
**Fix:** Add to render.yaml environment variables

### Health checks failing
**Cause:** Server not responding on correct port
**Fix:** Check Gunicorn is binding to `0.0.0.0:$PORT`

### Can't see errors in logs
**Cause:** Logging level too high
**Fix:** Check `LOGGING` configuration in settings.py

---

## Part 6: Performance Tuning

### Workers
```python
workers = max(2, multiprocessing.cpu_count())
```
- Render free tier: 2-3 workers
- Render paid tier: 4+ workers

### Timeout
```python
timeout = 60
```
- Increase if requests take longer
- Decrease if you want faster failure detection

### Keep-Alive
```python
keepalive = 2
```
- Reuse connections for better performance
- Reduce for more connection isolation

---

## Part 7: Monitoring & Alerts

### Key Metrics to Monitor
1. **Response Time** - Should be < 500ms for most requests
2. **Error Rate** - Should be < 1%
3. **Worker Health** - All workers should be active
4. **Database Connections** - Should not max out

### Recommended Tools
- Render's built-in logs
- Sentry (for error tracking)
- New Relic (for performance monitoring)
- Datadog (for comprehensive monitoring)

---

## Part 8: Security Best Practices

### Current Configuration
- ✓ HTTPS enforced in production
- ✓ Secure cookies enabled
- ✓ CSRF protection active
- ✓ XSS prevention enabled
- ✓ HSTS headers configured

### Additional Recommendations
1. Set strong `SECRET_KEY` (Render auto-generates)
2. Use environment variables for all secrets
3. Enable database backups
4. Monitor logs for suspicious activity
5. Keep dependencies updated

---

## Part 9: Maintenance

### Regular Tasks
- [ ] Check logs weekly for errors
- [ ] Update dependencies monthly
- [ ] Review security settings quarterly
- [ ] Test disaster recovery annually

### Deployment Updates
1. Make code changes locally
2. Test thoroughly
3. Commit to GitHub
4. Render auto-deploys on push
5. Monitor logs for issues

---

## Part 10: Support & Resources

### Render Documentation
- https://render.com/docs
- https://render.com/docs/deploy-django

### Django Documentation
- https://docs.djangoproject.com/en/6.0/
- https://docs.djangoproject.com/en/6.0/howto/deployment/

### Gunicorn Documentation
- https://docs.gunicorn.org/

### Common Issues
- See "Troubleshooting" section above
- Check Render logs first
- Review Django error messages
- Test locally before deploying

---

**Last Updated:** December 16, 2025
**Status:** Production Ready
**Version:** 1.0
