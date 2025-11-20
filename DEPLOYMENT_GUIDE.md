# Deployment Guide for Ripple

This guide covers deploying your Django application to various platforms.

## Prerequisites

1. **Environment Variables** - Create a `.env` file or set environment variables on your hosting platform
2. **Database** - PostgreSQL (recommended for production)
3. **Static Files** - Already configured with WhiteNoise
4. **Python Version** - Python 3.8+ (check with `python --version`)

## Required Environment Variables

Create a `.env` file or set these in your hosting platform:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Email Settings (for production)
USE_CONSOLE_EMAIL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Stripe (if using payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Google OAuth (if using social login)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Security (for production)
SECURE_SSL_REDIRECT=True
```

---

## Option 1: Railway (Recommended - Easy & Free Tier)

### Steps:

1. **Sign up at [Railway.app](https://railway.app)**

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo" (connect your GitHub)

3. **Add PostgreSQL Database**
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Railway will provide `DATABASE_URL` automatically

4. **Configure Environment Variables**
   - Go to your project → "Variables"
   - Add all required environment variables from above
   - Set `DEBUG=False`
   - Set `ALLOWED_HOSTS` to your Railway domain (e.g., `yourapp.railway.app`)

5. **Deploy**
   - Railway auto-detects Django
   - It will run: `python manage.py migrate` and `python manage.py collectstatic`
   - Your app will be live at `yourapp.railway.app`

### Railway-Specific Files (Optional)

Create `Procfile` in project root:
```
web: gunicorn ripple.wsgi:application --bind 0.0.0.0:$PORT
```

Create `runtime.txt` (if needed):
```
python-3.11.0
```

---

## Option 2: Render (Good Free Tier)

### Steps:

1. **Sign up at [Render.com](https://render.com)**

2. **Create New Web Service**
   - Connect your GitHub repository
   - Select "Web Service"

3. **Configure Build Settings**
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn ripple.wsgi:application`

4. **Add PostgreSQL Database**
   - Create new PostgreSQL database
   - Copy the "Internal Database URL" to `DATABASE_URL` environment variable

5. **Set Environment Variables**
   - Add all required variables in the "Environment" section
   - Set `DEBUG=False`
   - Set `ALLOWED_HOSTS` to your Render domain

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

---

## Option 3: Heroku (Paid, but Reliable)

### Steps:

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

4. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

5. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   # Add all other environment variables
   ```

6. **Create Procfile** (in project root)
   ```
   web: gunicorn ripple.wsgi:application
   release: python manage.py migrate
   ```

7. **Deploy**
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

---

## Option 4: DigitalOcean App Platform

### Steps:

1. **Sign up at [DigitalOcean](https://www.digitalocean.com)**

2. **Create App**
   - Go to "Apps" → "Create App"
   - Connect your GitHub repository

3. **Configure**
   - **Type**: Web Service
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Run Command**: `gunicorn ripple.wsgi:application --bind 0.0.0.0:8080`

4. **Add Database**
   - Add PostgreSQL database component
   - Set `DATABASE_URL` automatically

5. **Set Environment Variables**
   - Add all required variables
   - Set `DEBUG=False`

---

## Pre-Deployment Checklist

Before deploying, make sure to:

- [ ] Set `DEBUG=False` in production
- [ ] Set a strong `SECRET_KEY` (generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Configure PostgreSQL database
- [ ] Set up email service (Gmail SMTP or SendGrid)
- [ ] Configure Stripe keys (if using payments)
- [ ] Configure Google OAuth (if using social login)
- [ ] Run `python manage.py collectstatic` locally to test
- [ ] Run `python manage.py migrate` to ensure migrations work
- [ ] Test with `gunicorn ripple.wsgi:application` locally

---

## Post-Deployment Steps

1. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

2. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

3. **Collect Static Files** (if not automated)
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Set up Domain** (if using custom domain)
   - Add domain in hosting platform
   - Update `ALLOWED_HOSTS` environment variable
   - Configure DNS records

5. **Set up SSL/HTTPS**
   - Most platforms provide free SSL certificates
   - Ensure `SECURE_SSL_REDIRECT=True` in production

---

## Testing Deployment Locally

Before deploying, test with production-like settings:

```bash
# Set environment variables
export DEBUG=False
export SECRET_KEY=your-test-secret-key
export ALLOWED_HOSTS=localhost

# Run with Gunicorn
gunicorn ripple.wsgi:application

# Test static files
python manage.py collectstatic
```

---

## Troubleshooting

### Static Files Not Loading
- Ensure `STATIC_ROOT` is set correctly
- Run `python manage.py collectstatic`
- Check WhiteNoise is in `MIDDLEWARE`

### Database Connection Issues
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Check database is accessible from your hosting platform
- Ensure `psycopg2-binary` is in requirements.txt

### 500 Errors
- Check logs in your hosting platform
- Ensure `DEBUG=False` in production
- Verify all environment variables are set
- Check `ALLOWED_HOSTS` includes your domain

### Migration Issues
- Run `python manage.py migrate` manually
- Check for migration conflicts
- Ensure database user has proper permissions

---

## Recommended: Railway or Render

For beginners, I recommend **Railway** or **Render** because:
- ✅ Free tier available
- ✅ Easy setup
- ✅ Automatic deployments from GitHub
- ✅ Built-in PostgreSQL
- ✅ Free SSL certificates
- ✅ Good documentation

---

## Need Help?

- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Heroku Docs: https://devcenter.heroku.com/articles/getting-started-with-python

