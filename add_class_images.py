"""
Script to add thumbnail images to existing classes that don't have them.
This script will download placeholder images and add them to classes.

Note: This script uses Picsum Photos which provides placeholder images.
For truly topic-relevant images, consider:
1. Using Unsplash API with a free API key (requires registration)
2. Manually uploading relevant images through the admin interface
3. Using a paid image API service

Usage:
    python add_class_images.py
"""

import os
import sys
import django
import urllib.request
import tempfile
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from skills.models import TeachingClass, ClassTopic

# Image keywords mapping - maps class topics to search terms for relevant images
IMAGE_KEYWORDS = {
    # Programming languages
    'python': 'python,programming,code',
    'javascript': 'javascript,code,programming',
    'django': 'web,development,programming',
    'react': 'react,javascript,web,development',
    'vue.js': 'vue,javascript,web,development',
    'node.js': 'nodejs,server,backend',
    
    # Data & AI
    'data science': 'data,analysis,charts,graph',
    'machine learning': 'artificial,intelligence,neural,network',
    'pandas': 'data,analysis,spreadsheet',
    'tensorflow': 'machine,learning,neural,network',
    
    # Design
    'ui/ux': 'ui,design,interface,user,experience',
    'graphic design': 'graphic,design,creative,art',
    'photoshop': 'graphic,design,photo,editing',
    'illustrator': 'vector,graphic,design',
    'figma': 'ui,design,prototype',
    
    # Marketing & Business
    'digital marketing': 'marketing,social,media,business',
    'seo': 'search,engine,optimization,web',
    'content writing': 'writing,laptop,blog,content',
    'project management': 'planning,organization,team,work',
    
    # Media & Creative
    'photography': 'camera,photography,photo',
    'video editing': 'video,editing,film,production',
    'premiere pro': 'video,editing,film',
    'lightroom': 'photo,editing,photography',
    
    # Development
    'web development': 'web,development,programming,code',
    'backend development': 'server,backend,api,development',
    'mobile development': 'mobile,app,phone,development',
    'flutter': 'mobile,app,development',
    
    # Other
    'sql': 'database,server,data,storage',
    'database': 'database,server,data',
    'cybersecurity': 'security,lock,cyber,protection',
    'blender': '3d,modeling,animation,render',
    '3d modeling': '3d,modeling,animation',
    'public speaking': 'presentation,speaking,public,stage',
    'oop': 'programming,code,object,oriented',
    'rest apis': 'api,server,backend,development',
    'deployment': 'server,cloud,deployment,hosting',
}


def get_search_term(class_title, topics):
    """Get the best search term for finding a relevant image"""
    title_lower = class_title.lower()
    
    # First, try to match the title
    for keyword, search_terms in IMAGE_KEYWORDS.items():
        if keyword in title_lower:
            return search_terms
    
    # Then try topics
    if topics:
        for topic in topics:
            topic_lower = topic.lower()
            for keyword, search_terms in IMAGE_KEYWORDS.items():
                if keyword in topic_lower:
                    return search_terms
    
    # Extract key words from title as fallback
    words = title_lower.split()
    # Remove common words
    common_words = {'introduction', 'to', 'the', 'with', 'and', 'for', 'a', 'an', 'of', 'in', 'on', 'at', 'by'}
    relevant_words = [w for w in words if w not in common_words and len(w) > 3]
    if relevant_words:
        return ','.join(relevant_words[:3])
    
    return 'education,learning,class'


def get_class_image_url(class_title, topics, seed=None):
    """Generate an image URL based on class title and topics"""
    # Get search terms
    search_terms = get_search_term(class_title, topics)
    
    # Create a more specific seed based on the primary keyword
    # This ensures similar topics get similar (but not identical) images
    if seed is None:
        # Extract primary keyword from search terms
        primary_keyword = search_terms.split(',')[0] if ',' in search_terms else search_terms.split()[0]
        # Create a hash from the primary keyword for topic-based grouping
        seed = abs(hash(primary_keyword)) % 1000
    
    # Use Picsum Photos with seed for consistent, topic-based images
    # Note: Picsum Photos provides placeholder images, not actual topic-specific images
    # For real topic-specific images, you would need to use a paid API or manually upload images
    return f"https://picsum.photos/seed/{seed}/800/600"


def download_image(url, timeout=10):
    """Download an image from URL and return a file-like object"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            img_data = response.read()
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(img_data)
            temp_file.seek(0)
            return temp_file
    except Exception as e:
        try:
            print(f"  Warning: Could not download image: {e}")
        except UnicodeEncodeError:
            print(f"  Warning: Could not download image")
        return None


def main():
    # Get all published classes to update with relevant images
    classes_to_update = TeachingClass.objects.filter(is_published=True)
    
    total = classes_to_update.count()
    
    if total == 0:
        print('[OK] No published classes found!')
        return
    
    print(f'Found {total} published classes.')
    print('Updating images with relevant topic-based images...\n')
    
    updated_count = 0
    failed_count = 0
    
    for teaching_class in classes_to_update:
        try:
            # Delete existing thumbnail if it exists
            if teaching_class.thumbnail:
                try:
                    teaching_class.thumbnail.delete(save=False)
                except:
                    pass
            
            # Get topics for this class
            topics = list(teaching_class.topics.values_list('name', flat=True))
            
            # Get image URL based on class title and topics
            image_url = get_class_image_url(teaching_class.title, topics)
            
            # Download image
            img_file = download_image(image_url)
            
            if img_file:
                # Save thumbnail
                teaching_class.thumbnail.save(
                    f"{teaching_class.slug}_thumb.jpg",
                    File(img_file),
                    save=True
                )
                img_file.close()
                
                # Clean up temp file
                try:
                    os.unlink(img_file.name)
                except:
                    pass
                
                updated_count += 1
                try:
                    print(f'  [OK] Updated image for: {teaching_class.title}')
                except UnicodeEncodeError:
                    print(f'  [OK] Updated image for class ID: {teaching_class.id}')
            else:
                failed_count += 1
                try:
                    print(f'  [FAIL] Failed to update image for: {teaching_class.title}')
                except UnicodeEncodeError:
                    print(f'  [FAIL] Failed to update image for class ID: {teaching_class.id}')
                
        except Exception as e:
            failed_count += 1
            try:
                print(f'  [ERROR] Error updating image for {teaching_class.title}: {e}')
            except UnicodeEncodeError:
                print(f'  [ERROR] Error updating image for class ID: {teaching_class.id}')
    
    print(f'\n[OK] Successfully added images to {updated_count} classes!')
    if failed_count > 0:
        print(f'  [WARNING] Failed to add images to {failed_count} classes.')


if __name__ == '__main__':
    from django.db import models
    main()

