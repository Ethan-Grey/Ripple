# Quick Deployment Guide - Railway (Easiest Option)

## 🚀 Deploy in 5 Minutes

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your Ripple repository
4. Railway will automatically detect Django and start deploying

### Step 3: Add Database

1. In your Railway project, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway automatically sets `DATABASE_URL` - no configuration needed!

### Step 4: Set Environment Variables

In Railway project → **"Variables"** tab, add:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourapp.railway.app
```

**Generate Secret Key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 5: Deploy!

Railway will automatically:
- ✅ Install dependencies
- ✅ Run migrations
- ✅ Collect static files
- ✅ Start your app

Your app will be live at: `https://yourapp.railway.app`

---

## 🔧 Additional Setup (Optional)

### Add Email (Gmail SMTP)
```env
USE_CONSOLE_EMAIL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourapp.com
```

### Add Stripe (if using payments)
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Add Google OAuth (if using social login)
```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## ✅ That's It!

Your Django app is now live! 🎉

**Next Steps:**
- Create a superuser: Railway → Your Service → "Deploy Logs" → Run command: `python manage.py createsuperuser`
- Set up custom domain (optional)
- Configure email service for production

---

## 🆘 Need Help?

See `DEPLOYMENT_GUIDE.md` for detailed instructions and other hosting options.

