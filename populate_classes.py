"""
Script to populate realistic classes for the Ripple platform.
Run this after populating users.

Usage:
    python populate_classes.py [--count N] [--clear]
    
Options:
    --count N: Number of classes to create (default: 20)
    --clear: Delete all existing published classes before creating new ones
"""

import os
import sys
import django
import random
import argparse
import urllib.request
import tempfile
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from django.contrib.auth import get_user_model
from skills.models import TeachingClass, ClassTopic

User = get_user_model()

# Sample class data
CLASS_TEMPLATES = [
    {
        'title': 'Introduction to Python Programming',
        'short_description': 'Learn the fundamentals of Python programming from scratch',
        'full_description': 'This comprehensive course covers Python basics including variables, data types, control structures, functions, and object-oriented programming. Perfect for beginners who want to start their coding journey.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 180,
        'price_cents': 2999,
        'topics': ['Python Basics', 'Variables', 'Functions', 'OOP'],
        'is_tradeable': True,
    },
    {
        'title': 'Advanced Web Development with Django',
        'short_description': 'Master Django framework for building robust web applications',
        'full_description': 'Deep dive into Django framework covering models, views, templates, authentication, REST APIs, and deployment strategies. Build real-world projects.',
        'difficulty': TeachingClass.ADVANCED,
        'duration_minutes': 480,
        'price_cents': 4999,
        'topics': ['Django', 'Backend Development', 'REST APIs', 'Deployment'],
        'is_tradeable': False,
    },
    {
        'title': 'JavaScript Fundamentals',
        'short_description': 'Master JavaScript from basics to advanced concepts',
        'full_description': 'Comprehensive JavaScript course covering ES6+, async programming, DOM manipulation, and modern frameworks. Hands-on projects included.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 240,
        'price_cents': 3499,
        'topics': ['JavaScript', 'ES6+', 'Async Programming', 'DOM'],
        'is_tradeable': True,
    },
    {
        'title': 'Data Science with Python',
        'short_description': 'Learn data analysis, visualization, and machine learning',
        'full_description': 'Complete data science course using Python. Learn pandas, numpy, matplotlib, seaborn, and scikit-learn. Work with real datasets.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 360,
        'price_cents': 4499,
        'topics': ['Data Science', 'Pandas', 'Machine Learning', 'Visualization'],
        'is_tradeable': False,
    },
    {
        'title': 'React.js Complete Guide',
        'short_description': 'Build modern user interfaces with React',
        'full_description': 'Learn React from scratch. Cover hooks, context, routing, state management, and building production-ready applications.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 300,
        'price_cents': 3999,
        'topics': ['React', 'Hooks', 'State Management', 'Routing'],
        'is_tradeable': True,
    },
    {
        'title': 'UI/UX Design Principles',
        'short_description': 'Master the art of user interface and experience design',
        'full_description': 'Learn design thinking, user research, wireframing, prototyping, and creating beautiful, functional interfaces. Includes Figma tutorials.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 200,
        'price_cents': 2999,
        'topics': ['UI Design', 'UX Research', 'Figma', 'Prototyping'],
        'is_tradeable': True,
    },
    {
        'title': 'Machine Learning Fundamentals',
        'short_description': 'Introduction to machine learning algorithms and applications',
        'full_description': 'Learn supervised and unsupervised learning, neural networks, and deep learning. Implement algorithms from scratch and use TensorFlow.',
        'difficulty': TeachingClass.ADVANCED,
        'duration_minutes': 420,
        'price_cents': 5499,
        'topics': ['Machine Learning', 'Neural Networks', 'TensorFlow', 'Deep Learning'],
        'is_tradeable': False,
    },
    {
        'title': 'Graphic Design Mastery',
        'short_description': 'Create stunning visuals with professional design techniques',
        'full_description': 'Learn color theory, typography, composition, and design principles. Master Adobe Photoshop, Illustrator, and InDesign.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 280,
        'price_cents': 3799,
        'topics': ['Graphic Design', 'Photoshop', 'Illustrator', 'Typography'],
        'is_tradeable': True,
    },
    {
        'title': 'Digital Marketing Strategy',
        'short_description': 'Learn to grow your business with digital marketing',
        'full_description': 'Comprehensive guide to SEO, social media marketing, content marketing, email campaigns, and analytics. Real-world case studies.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 220,
        'price_cents': 3299,
        'topics': ['SEO', 'Social Media', 'Content Marketing', 'Analytics'],
        'is_tradeable': True,
    },
    {
        'title': 'Photography Essentials',
        'short_description': 'Master the art of photography from composition to editing',
        'full_description': 'Learn camera settings, lighting, composition rules, and post-processing. Includes practical shooting exercises and Lightroom tutorials.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 180,
        'price_cents': 2799,
        'topics': ['Photography', 'Composition', 'Lighting', 'Lightroom'],
        'is_tradeable': True,
    },
    {
        'title': 'Node.js Backend Development',
        'short_description': 'Build scalable server-side applications with Node.js',
        'full_description': 'Learn Express.js, RESTful APIs, authentication, database integration, and deployment. Build a complete backend application.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 320,
        'price_cents': 4299,
        'topics': ['Node.js', 'Express', 'REST APIs', 'MongoDB'],
        'is_tradeable': False,
    },
    {
        'title': 'Vue.js Framework Guide',
        'short_description': 'Build reactive web applications with Vue.js',
        'full_description': 'Complete Vue.js course covering components, routing, state management with Vuex, and building single-page applications.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 260,
        'price_cents': 3699,
        'topics': ['Vue.js', 'Components', 'Vuex', 'Routing'],
        'is_tradeable': True,
    },
    {
        'title': 'Cybersecurity Basics',
        'short_description': 'Protect systems and data from cyber threats',
        'full_description': 'Learn about common vulnerabilities, encryption, network security, ethical hacking basics, and security best practices.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 300,
        'price_cents': 4499,
        'topics': ['Cybersecurity', 'Encryption', 'Network Security', 'Ethical Hacking'],
        'is_tradeable': False,
    },
    {
        'title': 'Content Writing Masterclass',
        'short_description': 'Write engaging content that converts readers',
        'full_description': 'Learn copywriting, storytelling, SEO writing, and content strategy. Create blog posts, articles, and marketing copy that resonates.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 160,
        'price_cents': 2499,
        'topics': ['Copywriting', 'SEO Writing', 'Storytelling', 'Content Strategy'],
        'is_tradeable': True,
    },
    {
        'title': 'Video Editing with Premiere Pro',
        'short_description': 'Create professional videos with Adobe Premiere Pro',
        'full_description': 'Master video editing, color grading, audio mixing, and motion graphics. Learn to create engaging video content for any platform.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 240,
        'price_cents': 3499,
        'topics': ['Video Editing', 'Premiere Pro', 'Color Grading', 'Motion Graphics'],
        'is_tradeable': True,
    },
    {
        'title': 'Mobile App Development with Flutter',
        'short_description': 'Build cross-platform mobile apps with Flutter',
        'full_description': 'Learn Flutter and Dart to create beautiful, native mobile applications for iOS and Android. Build real apps with state management.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 380,
        'price_cents': 4799,
        'topics': ['Flutter', 'Dart', 'Mobile Development', 'State Management'],
        'is_tradeable': False,
    },
    {
        'title': 'SQL Database Design',
        'short_description': 'Master database design and SQL queries',
        'full_description': 'Learn relational database design, normalization, complex SQL queries, stored procedures, and database optimization techniques.',
        'difficulty': TeachingClass.INTERMEDIATE,
        'duration_minutes': 200,
        'price_cents': 2999,
        'topics': ['SQL', 'Database Design', 'Normalization', 'Query Optimization'],
        'is_tradeable': True,
    },
    {
        'title': '3D Modeling with Blender',
        'short_description': 'Create stunning 3D models and animations',
        'full_description': 'Learn Blender from basics to advanced techniques. Model, texture, light, and animate 3D scenes. Perfect for game development and animation.',
        'difficulty': TeachingClass.ADVANCED,
        'duration_minutes': 400,
        'price_cents': 4999,
        'topics': ['Blender', '3D Modeling', 'Animation', 'Texturing'],
        'is_tradeable': False,
    },
    {
        'title': 'Public Speaking Confidence',
        'short_description': 'Overcome fear and deliver powerful presentations',
        'full_description': 'Build confidence in public speaking. Learn storytelling, body language, voice modulation, and how to engage any audience.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 120,
        'price_cents': 1999,
        'topics': ['Public Speaking', 'Presentation Skills', 'Confidence', 'Storytelling'],
        'is_tradeable': True,
    },
    {
        'title': 'Project Management Fundamentals',
        'short_description': 'Lead projects successfully from start to finish',
        'full_description': 'Learn project planning, team management, risk assessment, agile methodologies, and tools like Jira and Trello.',
        'difficulty': TeachingClass.BEGINNER,
        'duration_minutes': 180,
        'price_cents': 2799,
        'topics': ['Project Management', 'Agile', 'Team Leadership', 'Risk Management'],
        'is_tradeable': True,
    },
]

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
    
    # Use a seed-based approach with Picsum Photos
    # Generate a consistent seed from the search terms so same topic = same image
    if seed is None:
        # Create a hash from search terms for consistency
        seed = abs(hash(search_terms)) % 1000
    
    # Use Picsum Photos with seed for consistent, topic-based images
    # The seed ensures the same topic always gets the same image
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
    parser = argparse.ArgumentParser(description='Populate the database with sample teaching classes')
    parser.add_argument(
        '--count',
        type=int,
        default=20,
        help='Number of classes to create (default: 20)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Delete all existing published classes before creating new ones'
    )
    
    args = parser.parse_args()
    count = args.count
    clear = args.clear

    # Get or create users for teaching
    users = User.objects.all()
    if not users.exists():
        print('⚠️  No users found. Creating sample users...')
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f'teacher{i}',
                defaults={
                    'email': f'teacher{i}@example.com',
                    'first_name': f'Teacher {i}',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                print(f'✓ Created user: {user.username}')
        users = User.objects.all()

    # Clear existing classes if requested
    if clear:
        deleted_count = TeachingClass.objects.filter(is_published=True).delete()[0]
        print(f'⚠️  Deleted {deleted_count} existing published classes.')

    # Create classes
    print(f'Creating {count} classes...')
    created_count = 0
    for i in range(count):
        # Select a random template or create variations
        template = random.choice(CLASS_TEMPLATES)
        
        # Create variations for multiple classes
        if i >= len(CLASS_TEMPLATES):
            # Create variations of existing templates
            title = f"{template['title']} - Part {i // len(CLASS_TEMPLATES) + 1}"
            slug = slugify(title)
        else:
            title = template['title']
            slug = slugify(title)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while TeachingClass.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Select a random teacher
        teacher = random.choice(users)

        # Create the class
        teaching_class = TeachingClass.objects.create(
            title=title,
            slug=slug,
            short_description=template['short_description'],
            full_description=template['full_description'],
            difficulty=template['difficulty'],
            duration_minutes=template['duration_minutes'],
            price_cents=template['price_cents'],
            is_tradeable=template['is_tradeable'],
            is_published=True,
            teacher=teacher,
            created_at=timezone.now() - timedelta(days=random.randint(0, 90)),
        )
        
        # Get image URL for this class (use class ID as seed for consistency)
        image_url = get_class_image_url(title, template['topics'], seed=teaching_class.id)
        
        # Download and add thumbnail image
        try:
            img_file = download_image(image_url)
            if img_file:
                teaching_class.thumbnail.save(
                    f"{slug}_thumb.jpg",
                    File(img_file),
                    save=True
                )
                img_file.close()
                # Clean up temp file
                try:
                    os.unlink(img_file.name)
                except:
                    pass
        except Exception as e:
            try:
                print(f"  Warning: Could not add image for {title}: {e}")
            except UnicodeEncodeError:
                print(f"  Warning: Could not add image for class")

        # Add topics
        for topic_name in template['topics']:
            ClassTopic.objects.create(
                name=topic_name,
                teaching_class=teaching_class
            )

        created_count += 1
        if created_count % 5 == 0:
            print(f'  Created {created_count} classes...')

    print(f'\n✓ Successfully created {created_count} published classes!')
    print(f'  You can now view them at /classes/')


if __name__ == '__main__':
    main()

