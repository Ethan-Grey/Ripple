"""
Management command to check database configuration and verify data persistence.
Run this on Railway to diagnose database issues.
Usage: python manage.py check_database
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from skills.models import TeachingClass
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Check database configuration and verify data persistence'

    def handle(self, *args, **options):
        """Check database configuration and test persistence"""
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("DATABASE DIAGNOSTICS"))
        self.stdout.write("=" * 60)
        
        # Check database backend
        db_backend = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default'].get('NAME', 'N/A')
        
        self.stdout.write(f"\n1. Database Backend: {db_backend}")
        self.stdout.write(f"   Database Name: {db_name}")
        
        # Check DATABASE_URL
        database_url = os.getenv('DATABASE_URL', 'NOT SET')
        if database_url != 'NOT SET':
            # Mask password for security
            if '@' in database_url:
                parts = database_url.split('@')
                if ':' in parts[0]:
                    user_pass = parts[0].split(':')
                    if len(user_pass) > 2:
                        masked_url = ':'.join(user_pass[:-1]) + ':***@' + '@'.join(parts[1:])
                    else:
                        masked_url = user_pass[0] + ':***@' + '@'.join(parts[1:])
                else:
                    masked_url = database_url
            else:
                masked_url = database_url
            self.stdout.write(f"   DATABASE_URL: {masked_url[:80]}...")
        else:
            self.stdout.write(self.style.WARNING(
                f"   DATABASE_URL: NOT SET (using SQLite - DATA WILL BE LOST ON DEPLOY!)"
            ))
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS("\n2. Database Connection: ✓ SUCCESS"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n2. Database Connection: ✗ FAILED - {str(e)}"))
        
        # Count classes
        try:
            total_classes = TeachingClass.objects.count()
            published_classes = TeachingClass.objects.filter(is_published=True).count()
            unpublished_classes = TeachingClass.objects.filter(is_published=False).count()
            
            self.stdout.write(f"\n3. TeachingClass Statistics:")
            self.stdout.write(f"   Total classes: {total_classes}")
            self.stdout.write(f"   Published: {published_classes}")
            self.stdout.write(f"   Unpublished: {unpublished_classes}")
            
            # Show recent classes
            self.stdout.write(f"\n4. Recent Classes (last 5):")
            recent = TeachingClass.objects.order_by('-created_at')[:5]
            for cls in recent:
                status = "✓ PUBLISHED" if cls.is_published else "✗ UNPUBLISHED"
                style = self.style.SUCCESS if cls.is_published else self.style.WARNING
                self.stdout.write(style(f"   [{status}] {cls.title} by {cls.teacher.username} (ID: {cls.id})"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n3. Error querying classes: {str(e)}"))
        
        # Check if using SQLite (ephemeral on Railway)
        if 'sqlite' in db_backend.lower():
            self.stdout.write(self.style.ERROR(
                f"\n⚠️  WARNING: Using SQLite database!"
            ))
            self.stdout.write(self.style.ERROR(
                "   SQLite files are EPHEMERAL on Railway and will be LOST on redeploy!"
            ))
            self.stdout.write(self.style.ERROR(
                "   You MUST use PostgreSQL for persistent storage."
            ))
            self.stdout.write(self.style.ERROR(
                "   Set DATABASE_URL environment variable in Railway."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✓ Using persistent database (PostgreSQL)"))
        
        self.stdout.write("\n" + "=" * 60)

