# Render Deployment - Quick Reference

## What Was Wrong
- ❌ Render using Python 3.13 (incompatible)
- ❌ Build command missing `cd demodev`
- ❌ Start command missing `cd demodev`
- ❌ No `runtime.txt` to specify Python version
- ❌ `pywin32` in requirements (Windows-only)

## What Was Fixed
- ✅ Created `runtime.txt` with Python 3.11.9
- ✅ Updated `render.yaml` with correct paths
- ✅ Cleaned `requirements.txt` (removed Windows packages)
- ✅ Created `Procfile` as backup

## Files Changed
```
runtime.txt                    ← NEW
requirements.txt               ← UPDATED
demodev/render.yaml            ← UPDATED
demodev/Procfile               ← NEW
```

## Correct Gunicorn Command
```bash
cd demodev && gunicorn demodev.wsgi:application
```

## Test Locally
```bash
cd demodev
gunicorn demodev.wsgi:application
# Should start without errors
```

## Deploy Steps
1. Commit changes:
   ```bash
   git add runtime.txt requirements.txt demodev/render.yaml demodev/Procfile
   git commit -m "Fix Render deployment"
   git push origin main
   ```

2. In Render Dashboard:
   - Click "Manual Deploy"
   - Monitor logs
   - Verify app loads

## Key Configuration

**Build Command:**
```
cd demodev && pip install -r ../requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command:**
```
cd demodev && gunicorn demodev.wsgi:application
```

**Python Version:**
```
3.11.9 (via runtime.txt)
```

**Environment Variables:**
- `DEBUG=False`
- `SECRET_KEY=<auto>`
- `DATABASE_URL=<auto>`
- `ALLOWED_HOSTS=*.onrender.com,localhost,127.0.0.1`

## Verify After Deploy
- [ ] App loads at `https://your-app.onrender.com`
- [ ] Admin works at `/admin`
- [ ] API responds at `/api/`
- [ ] No errors in Render logs
