"""
Script to migrate data from local SQLite database to Railway PostgreSQL database.

Usage:
1. Set DATABASE_URL environment variable to your Railway PostgreSQL connection string
2. Make sure your local SQLite database (db.sqlite3) has the data you want to migrate
3. Run: python migrate_to_postgresql.py

This will:
- Export all data from SQLite to JSON fixtures
- Switch to PostgreSQL
- Run migrations on PostgreSQL
- Import all data into PostgreSQL
"""
import os
import sys
import django
import json
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings
from django.db import connection

def export_sqlite_data():
    """Export all data from SQLite to JSON fixtures"""
    print("=" * 60)
    print("STEP 1: Exporting data from SQLite database...")
    print("=" * 60)
    
    # Temporarily switch to SQLite
    original_db = settings.DATABASES['default'].copy()
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(__file__).parent / 'db.sqlite3',
    }
    
    # Export all apps
    apps_to_export = [
        'auth', 'contenttypes', 'sessions',
        'users', 'skills', 'communities', 'chat',
        'account', 'socialaccount', 'sites',
    ]
    
    fixture_file = 'migration_data.json'
    
    try:
        # Use dumpdata to export
        with open(fixture_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', *apps_to_export, stdout=f, natural_foreign=True, natural_primary=True)
        print(f"✓ Data exported to {fixture_file}")
        
        # Check file size
        file_size = Path(fixture_file).stat().st_size
        print(f"  File size: {file_size / 1024:.2f} KB")
        
        return fixture_file
    except Exception as e:
        print(f"✗ Error exporting data: {e}")
        return None
    finally:
        # Restore original database config
        settings.DATABASES['default'] = original_db

def import_to_postgresql(fixture_file):
    """Import data from JSON fixture to PostgreSQL"""
    print("\n" + "=" * 60)
    print("STEP 2: Importing data to PostgreSQL database...")
    print("=" * 60)
    
    if not Path(fixture_file).exists():
        print(f"✗ Fixture file {fixture_file} not found!")
        return False
    
    # Verify we're using PostgreSQL now
    current_engine = settings.DATABASES['default']['ENGINE']
    if 'postgresql' not in current_engine.lower():
        print("⚠️  WARNING: Not using PostgreSQL! Current engine:", current_engine)
        print("   Make sure DATABASE_URL is set to your Railway PostgreSQL connection")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        # Run migrations first
        print("\nRunning migrations on PostgreSQL...")
        call_command('migrate', verbosity=1)
        print("✓ Migrations completed")
        
        # Load the fixture
        print(f"\nLoading data from {fixture_file}...")
        call_command('loaddata', fixture_file, verbosity=2)
        print("✓ Data imported successfully!")
        
        return True
    except Exception as e:
        print(f"✗ Error importing data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main migration process"""
    print("\n" + "=" * 60)
    print("DATABASE MIGRATION: SQLite → PostgreSQL")
    print("=" * 60)
    print()
    
    # Check if SQLite database exists
    sqlite_db = Path(__file__).parent / 'db.sqlite3'
    if not sqlite_db.exists():
        print("✗ SQLite database (db.sqlite3) not found!")
        print("   Nothing to migrate.")
        return
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️  DATABASE_URL not set!")
        print("   Set it to your Railway PostgreSQL connection string:")
        print("   export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return
    
    print(f"SQLite database: {sqlite_db} ({sqlite_db.stat().st_size / 1024:.2f} KB)")
    print(f"PostgreSQL URL: {database_url.split('@')[0]}@***")
    print()
    
    confirm = input("Proceed with migration? (y/n): ")
    if confirm.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Step 1: Export from SQLite
    fixture_file = export_sqlite_data()
    if not fixture_file:
        print("\n✗ Migration failed at export step")
        return
    
    # Step 2: Import to PostgreSQL
    success = import_to_postgresql(fixture_file)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ MIGRATION COMPLETE!")
        print("=" * 60)
        print("\nYour data has been migrated to PostgreSQL.")
        print("You can now delete the fixture file if you want:")
        print(f"  rm {fixture_file}")
    else:
        print("\n" + "=" * 60)
        print("✗ MIGRATION FAILED")
        print("=" * 60)
        print("\nThe fixture file is saved, so you can try again later.")
        print(f"Fixture file: {fixture_file}")

if __name__ == '__main__':
    main()

