# How to Migrate Data from SQLite to Railway PostgreSQL

## Quick Method (Easiest)

### Step 1: Get Your Railway DATABASE_URL

1. Go to Railway dashboard → Your PostgreSQL service
2. Click on "Variables" tab
3. Copy the `DATABASE_URL` value (it looks like: `postgresql://postgres:password@host:port/railway`)

### Step 2: Run Migration on Your Local Machine

**On Windows PowerShell:**
```powershell
# Set the Railway PostgreSQL connection string
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"

# Run the migration script
python migrate_to_postgresql.py
```

**On Windows Command Prompt:**
```cmd
set DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway
python migrate_to_postgresql.py
```

**On Mac/Linux:**
```bash
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"
python migrate_to_postgresql.py
```

The script will:
- Export data from your local SQLite database
- Connect to Railway PostgreSQL
- Import all data to Railway

---

## Option 2: Using Railway CLI

If you have Railway CLI installed:

```bash
# Connect to Railway
railway link

# Run the migration script on Railway (it will use Railway's DATABASE_URL automatically)
railway run python migrate_to_postgresql.py
```

---

## Option 3: Manual Steps

If you prefer to do it step by step:

### 1. Export from local SQLite:
```bash
python manage.py dumpdata --natural-foreign --natural-primary -o data.json
```

### 2. Connect to Railway PostgreSQL and import:
```bash
# Set Railway DATABASE_URL
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"

# Run migrations
python manage.py migrate

# Import data
python manage.py loaddata data.json
```

---

## Troubleshooting

**Error: "DATABASE_URL not set"**
- Make sure you've set the environment variable before running the script
- On Windows, use `$env:DATABASE_URL` in PowerShell or `set DATABASE_URL` in CMD

**Error: "Connection refused"**
- Check that your Railway PostgreSQL is running
- Verify the DATABASE_URL is correct
- Make sure you're using the external connection string (not internal)

**Error: "SSL required"**
- Railway PostgreSQL requires SSL - the script should handle this automatically
- If issues persist, make sure `psycopg2-binary` is installed

---

## Important Notes

- Your local SQLite database (`db.sqlite3`) will NOT be changed - it's read-only during export
- The migration creates a backup JSON file (`migration_data.json`) that you can keep or delete
- After migration, Railway PostgreSQL will have all your data
- Your local SQLite database remains intact for local development

