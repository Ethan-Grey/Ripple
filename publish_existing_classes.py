"""
Script to publish all existing unpublished classes.
Run this after deploying the change to make existing classes visible.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from skills.models import TeachingClass

def publish_all_classes():
    """Publish all unpublished classes"""
    unpublished_classes = TeachingClass.objects.filter(is_published=False)
    count = unpublished_classes.count()
    
    if count == 0:
        print("No unpublished classes found.")
        return
    
    print(f"Found {count} unpublished class(es). Publishing them...")
    
    unpublished_classes.update(is_published=True)
    
    print(f"✓ Successfully published {count} class(es)!")
    print("\nPublished classes:")
    for cls in TeachingClass.objects.filter(is_published=True).order_by('-created_at')[:10]:
        print(f"  - {cls.title} by {cls.teacher.username}")

if __name__ == '__main__':
    publish_all_classes()

