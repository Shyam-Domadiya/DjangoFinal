# Render.com Deployment Guide

This guide walks you through deploying your Twitter DM application to Render.com.

## Prerequisites

1. A Render.com account (free tier available)
2. Your project pushed to GitHub
3. PostgreSQL database (Render provides this)

## Step-by-Step Deployment

### 1. Push Your Code to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a New Web Service on Render

1. Go to [render.com](https://render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Select the repository containing your project

### 3. Configure the Web Service

Fill in the following settings:

- **Name**: `twitter-dm-app` (or your preferred name)
- **Environment**: `Python 3.11`
- **Build Command**: 
  ```
  pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
  ```
- **Start Command**: 
  ```
  gunicorn demodev.wsgi:application
  ```
- **Plan**: Free (or paid if you prefer)

### 4. Add Environment Variables

In the Render dashboard, add these environment variables:

```
DEBUG=False
SECRET_KEY=<generate-a-secure-key>
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=<will-be-auto-populated-by-Render>
```

To generate a secure SECRET_KEY, run:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Create a PostgreSQL Database

1. In Render dashboard, click "New +" and select "PostgreSQL"
2. Configure:
   - **Name**: `twitter-db`
   - **Database**: `twitter_db`
   - **User**: `twitter_user`
   - **Plan**: Free
3. Once created, Render will automatically set the `DATABASE_URL` environment variable

### 6. Deploy

1. Click "Create Web Service"
2. Render will automatically start the build process
3. Monitor the deployment in the "Logs" tab
4. Once deployment is complete, your app will be live at `https://your-app-name.onrender.com`

## Post-Deployment

### Create a Superuser

After deployment, create an admin user:

1. Go to Render dashboard
2. Click on your web service
3. Click "Shell" tab
4. Run:
   ```bash
   python manage.py createsuperuser
   ```

### Access Admin Panel

Visit `https://your-app-name.onrender.com/admin` and log in with your superuser credentials.

## Troubleshooting

### Build Fails

Check the build logs in Render dashboard. Common issues:
- Missing dependencies in `requirements.txt`
- Incorrect Python version
- Database connection issues

### Static Files Not Loading

Ensure `STATIC_ROOT` is set correctly and `collectstatic` runs during build.

### Database Connection Issues

Verify `DATABASE_URL` is set correctly in environment variables.

### Application Crashes

Check the logs in Render dashboard for error messages.

## Important Notes

- **Free Tier Limitations**: 
  - Web service spins down after 15 minutes of inactivity
  - PostgreSQL database has limited storage
  - Limited compute resources

- **Production Considerations**:
  - Use a paid plan for production applications
  - Set up proper monitoring and logging
  - Configure email for notifications
  - Use a CDN for static files if needed

## Updating Your Application

To deploy updates:

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```
3. Render will automatically redeploy your application

## Additional Resources

- [Render Django Deployment Guide](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [Gunicorn Documentation](https://gunicorn.org/)
