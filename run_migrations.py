#!/usr/bin/env python
"""
Smart migration script for Railway.
Handles the case where tables exist but migrations haven't been recorded.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection, transaction

def check_table_exists(table_name):
    """Check if a table exists in the database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, [table_name])
            return cursor.fetchone()[0]
    except Exception:
        return False

def main():
    # Check if key tables exist
    content_type_exists = check_table_exists('django_content_type')
    migrations_table_exists = check_table_exists('django_migrations')
    
    if content_type_exists:
        # Tables exist - try --fake-initial to sync migration state
        print("Database tables detected. Syncing migration state with --fake-initial...")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--noinput', '--fake-initial'])
        except SystemExit as e:
            # Migration command completed (SystemExit with code 0 = success)
            if e.code == 0:
                print("Migrations synced successfully!")
            else:
                print(f"Migration completed with code {e.code}")
                raise
    else:
        # Fresh database - run normal migrations
        print("No existing tables found. Running normal migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])

if __name__ == '__main__':
    main()

