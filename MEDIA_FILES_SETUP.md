# Media Files Setup for Production

## Problem
By default, uploaded files (profile pictures, etc.) are stored on Railway's ephemeral filesystem, which means:
- ❌ Files are **lost when the container restarts or redeploys**
- ❌ Files can't be uploaded/served properly in production

## Solution: Railway Volume Storage (Recommended)

Railway volumes provide persistent storage that survives redeploys.

### Step 1: Add Volume to Railway

1. Go to your Railway project
2. Click **"+ New"** → **"Volume"**
3. Name it: `media-storage`
4. Mount path: `/data` (or leave default)
5. Click **"Add"**

### Step 2: Connect Volume to Your Service

1. Click on your **Ripple** service
2. Go to **"Settings"** tab
3. Scroll to **"Volumes"** section
4. Click **"Add Volume"**
5. Select your `media-storage` volume
6. Set mount path to: `/data`
7. Save

### Step 3: Set Environment Variable (Optional)

If your volume uses a different mount path, set:
- **Key**: `RAILWAY_VOLUME_MOUNT_PATH`
- **Value**: `/data` (or your custom path)

### Step 4: Deploy

The code will automatically detect the volume and use it for media storage.

---

## Alternative: Cloud Storage (Better for Scale)

For better performance and scalability, consider using cloud storage:

### Option A: AWS S3

1. **Install django-storages:**
   ```bash
   pip install django-storages boto3
   ```

2. **Add to requirements.txt:**
   ```
   django-storages==1.14.2
   boto3==1.34.0
   ```

3. **Update settings.py:**
   ```python
   # Add to INSTALLED_APPS
   'storages',
   
   # Media files with S3
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
   AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
   AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
   AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
   AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
   MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
   ```

4. **Set environment variables in Railway:**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_STORAGE_BUCKET_NAME`
   - `AWS_S3_REGION_NAME`

### Option B: Cloudinary (Easiest)

1. **Install:**
   ```bash
   pip install django-cloudinary-storage
   ```

2. **Add to requirements.txt:**
   ```
   django-cloudinary-storage==0.3.0
   ```

3. **Update settings.py:**
   ```python
   # Add to INSTALLED_APPS
   'cloudinary_storage',
   'cloudinary',
   
   # Media files
   DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
   CLOUDINARY_STORAGE = {
       'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
       'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
       'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
   }
   ```

4. **Set environment variables:**
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`

---

## Current Setup (What I Fixed)

✅ **Media files are now served in production** - Updated `urls.py` to serve media files even when `DEBUG=False`

✅ **Automatic volume detection** - Code automatically uses Railway volume if available

✅ **Fallback to project directory** - If no volume, uses project directory (ephemeral but works)

---

## Testing

After deploying:

1. Try uploading a profile picture
2. Check if it displays correctly
3. Verify the file persists after a redeploy (if using volume)

---

## Troubleshooting

### Files still not uploading?
- Check Railway logs for errors
- Verify volume is mounted correctly
- Check file permissions

### Files upload but don't display?
- Verify `MEDIA_URL` is correct
- Check browser console for 404 errors
- Ensure media serving is enabled in `urls.py`

### Files lost after redeploy?
- You need to set up Railway volume storage (see Step 1 above)
- Or switch to cloud storage (S3/Cloudinary)

---

## Recommendation

For production, I recommend:
1. **Short term**: Use Railway volume storage (easy, free)
2. **Long term**: Migrate to cloud storage (S3 or Cloudinary) for better performance and reliability

