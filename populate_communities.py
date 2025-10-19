"""
Script to populate realistic communities for the Ripple platform.
Run this after populating users and skills.
"""

import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from django.contrib.auth import get_user_model
from communities.models import Community
from skills.models import Skill

User = get_user_model()

# Community templates organized by skill type
COMMUNITY_TEMPLATES = {
    # Programming & Tech
    'Python': [
        ('Python Enthusiasts', 'A vibrant community for Python lovers of all levels. Share projects, ask questions, and collaborate on Python development.'),
        ('Django Developers Hub', 'Connect with fellow Django developers. Discuss best practices, troubleshoot issues, and share Django tips.'),
        ('Python for Data Science', 'Explore Python in data science, machine learning, and AI. Share insights and learn together.'),
        ('Beginner Python Circle', 'A supportive space for those just starting with Python. No question is too basic!'),
    ],
    'JavaScript': [
        ('JavaScript Masters', 'Advanced JavaScript discussions, ES6+, async programming, and cutting-edge frameworks.'),
        ('React Community', 'Everything React: hooks, state management, performance optimization, and best practices.'),
        ('Node.js Developers', 'Backend JavaScript with Node.js. APIs, microservices, and server-side development.'),
        ('Frontend Wizards', 'Modern frontend development: JavaScript, TypeScript, HTML5, CSS3, and frameworks.'),
    ],
    'Web Development': [
        ('Full Stack Developers', 'From frontend to backend, databases to deployment. Full stack development discussions.'),
        ('Web Design & UX', 'Combining development with design. Create beautiful, user-friendly web experiences.'),
        ('Modern Web Technologies', 'Stay updated with latest web trends: PWAs, Web Components, JAMstack, and more.'),
    ],
    
    # Creative Skills
    'Photography': [
        ('Lens & Light', 'Photography enthusiasts sharing techniques, equipment reviews, and stunning shots.'),
        ('Portrait Photography Club', 'Master the art of portrait photography. Lighting, posing, and post-processing tips.'),
        ('Nature & Landscape', 'Capture the beauty of nature. Share your landscape photography and learn from others.'),
        ('Street Photography', 'Urban photography, candid moments, and the art of capturing life on the streets.'),
    ],
    'Graphic Design': [
        ('Design Collective', 'Professional designers sharing work, feedback, and industry insights.'),
        ('Logo & Brand Identity', 'Specialize in branding, logo design, and visual identity systems.'),
        ('Digital Art & Illustration', 'From concept to final artwork. Share your digital creations and techniques.'),
    ],
    'Music Production': [
        ('Beat Makers United', 'Hip-hop, electronic, and modern beat production. Share beats and production tips.'),
        ('Home Studio Setup', 'Building and optimizing your home recording studio. Equipment, acoustics, and workflows.'),
        ('Music Theory for Producers', 'Learn and discuss music theory to enhance your productions.'),
    ],
    'Video Editing': [
        ('Video Editors Guild', 'Professional video editing techniques, software tutorials, and project showcases.'),
        ('YouTube Creators', 'Content creation for YouTube. Editing styles, storytelling, and audience growth.'),
        ('Color Grading Masters', 'Advanced color grading and color correction techniques.'),
    ],
    
    # Languages
    'Spanish': [
        ('Spanish Language Exchange', '¡Habla español! Practice conversational Spanish with native and learning speakers.'),
        ('Spanish Culture & Language', 'Learn Spanish through culture, music, movies, and authentic conversations.'),
        ('Business Spanish', 'Professional Spanish for business, presentations, and corporate communications.'),
    ],
    'French': [
        ('Bonjour French!', 'Learn and practice French in a friendly, supportive community.'),
        ('French Film Club', 'Watch and discuss French cinema while improving your language skills.'),
        ('French for Travelers', 'Practical French for travel, dining, and everyday situations.'),
    ],
    'Japanese': [
        ('日本語 Japanese Learners', 'From hiragana to kanji. Support each other in learning Japanese.'),
        ('Anime & Japanese Culture', 'Learn Japanese through anime, manga, and Japanese pop culture.'),
        ('Japanese Business Etiquette', 'Business Japanese and professional communication in Japanese culture.'),
    ],
    
    # Business & Marketing
    'Digital Marketing': [
        ('Digital Marketing Pros', 'SEO, SEM, social media, content marketing, and digital strategy discussions.'),
        ('Social Media Managers', 'Share campaigns, analytics insights, and social media trends.'),
        ('Content Creators Network', 'Content strategy, creation, and distribution across all platforms.'),
    ],
    'Entrepreneurship': [
        ('Startup Founders Circle', 'Connect with fellow entrepreneurs. Share challenges, victories, and advice.'),
        ('Small Business Owners', 'Support network for small business owners. Marketing, finance, and growth strategies.'),
        ('Side Hustle Community', 'Building businesses while working full-time. Share your journey!'),
    ],
    
    # Fitness & Wellness
    'Yoga': [
        ('Yoga Journey', 'Practice yoga together, share sequences, and discuss philosophy and mindfulness.'),
        ('Beginners Yoga Flow', 'Starting your yoga practice? Join us for support and gentle guidance.'),
        ('Advanced Asana Practice', 'Challenging poses, inversions, and advanced yoga techniques.'),
    ],
    'Fitness Training': [
        ('Strength & Conditioning', 'Weightlifting, powerlifting, and building strength. Share workouts and progress.'),
        ('Home Workout Heroes', 'Get fit at home with minimal equipment. Bodyweight and home training.'),
        ('Running Community', 'Runners of all levels. Share routes, training plans, and race experiences.'),
    ],
    'Cooking': [
        ('Home Chefs Network', 'Share recipes, cooking techniques, and delicious food photos.'),
        ('Baking Brigade', 'From bread to pastries. Master the art and science of baking.'),
        ('Healthy Cooking', 'Nutritious, delicious recipes for a healthy lifestyle.'),
        ('International Cuisine', 'Explore cooking from around the world. Share cultural dishes and techniques.'),
    ],
    
    # Arts & Crafts
    'Drawing': [
        ('Daily Sketchers', 'Practice drawing daily. Share sketches and get constructive feedback.'),
        ('Digital Art Community', 'Digital drawing, painting, and illustration. Software tips and techniques.'),
        ('Portrait Drawing Workshop', 'Master portrait drawing from beginner to advanced techniques.'),
    ],
    'Painting': [
        ('Artists Studio', 'Painters sharing work, techniques, and inspiration across all mediums.'),
        ('Watercolor Wonders', 'The beautiful world of watercolor painting. Share techniques and paintings.'),
        ('Abstract Artists', 'Explore abstract and contemporary painting styles and concepts.'),
    ],
    'Woodworking': [
        ('Woodworkers Guild', 'Furniture making, woodturning, carving, and all things woodworking.'),
        ('Beginner Woodshop', 'Starting woodworking? Learn fundamentals and basic projects here.'),
        ('Fine Furniture Makers', 'Advanced furniture design and craftsmanship. Share your masterpieces.'),
    ],
    
    # Other Skills
    'Writing': [
        ('Creative Writers Circle', 'Fiction, poetry, creative non-fiction. Share your writing and get feedback.'),
        ('Freelance Writers', 'Professional writing, content creation, and building a writing career.'),
        ('Novel Writing Workshop', 'Working on a novel? Share chapters, get feedback, and stay motivated.'),
    ],
    'Public Speaking': [
        ('Toastmasters Network', 'Improve public speaking and presentation skills in a supportive environment.'),
        ('Presentation Masters', 'Create and deliver impactful presentations. Tips, templates, and techniques.'),
    ],
    'Data Science': [
        ('Data Science Hub', 'Machine learning, AI, statistical analysis, and data visualization.'),
        ('Python for Data Analysis', 'Using Python for data analysis, pandas, numpy, and matplotlib.'),
        ('ML Engineers Forum', 'Machine learning engineering, model deployment, and MLOps.'),
    ],
    'Gaming': [
        ('Game Development', 'Create games! Unity, Unreal, game design, and indie development.'),
        ('Retro Gaming Club', 'Celebrate classic games and gaming history.'),
        ('E-Sports Community', 'Competitive gaming, tournaments, and professional gaming discussions.'),
    ],
}

# Generic community names that work for any skill
GENERIC_TEMPLATES = [
    ('{skill} Learners Hub', 'A welcoming community for everyone learning {skill}. Share resources and support each other.'),
    ('{skill} Experts Network', 'Advanced discussions and professional insights for {skill} experts.'),
    ('{skill} Study Group', 'Study and practice {skill} together. Collaborative learning and peer support.'),
    ('{skill} Enthusiasts', 'Passionate about {skill}? Join fellow enthusiasts to share knowledge and experiences.'),
    ('The {skill} Collective', 'A diverse community united by interest in {skill}. All levels welcome!'),
    ('{skill} Mastery', 'Dedicated to mastering {skill}. Share techniques, ask questions, grow together.'),
]


def populate_communities():
    """Create realistic communities with members."""
    
    print("Starting community population...")
    
    # Get all users and skills
    users = list(User.objects.all())
    skills = list(Skill.objects.all())
    
    if not users:
        print("ERROR: No users found! Please run populate_demographic_users.py first.")
        return
    
    if not skills:
        print("ERROR: No skills found! Please create some skills first.")
        return
    
    print(f"Found {len(users)} users and {len(skills)} skills")
    
    # Clear existing communities
    existing_count = Community.objects.count()
    if existing_count > 0:
        print(f"WARNING: Found {existing_count} existing communities. Deleting them...")
        Community.objects.all().delete()
        print(f"Deleted {existing_count} communities")
    
    communities_created = 0
    
    # Create communities for each skill
    for skill in skills:
        # Check if we have specific templates for this skill
        if skill.name in COMMUNITY_TEMPLATES:
            templates = COMMUNITY_TEMPLATES[skill.name]
            num_communities = len(templates)
        else:
            # Use generic templates
            templates = random.sample(GENERIC_TEMPLATES, min(2, len(GENERIC_TEMPLATES)))
            num_communities = len(templates)
        
        # Create communities for this skill
        for name_template, desc_template in templates[:num_communities]:
            # Format the name and description with skill name
            name = name_template.format(skill=skill.name) if '{skill}' in name_template else name_template
            description = desc_template.format(skill=skill.name) if '{skill}' in desc_template else desc_template
            
            # Pick a random creator from users who have this skill
            skill_users = [u for u in users if u.user_skills.filter(skill=skill).exists()]
            
            if not skill_users:
                # If no users have this skill, pick any random user
                creator = random.choice(users)
            else:
                creator = random.choice(skill_users)
            
            # Create the community with a random creation date (within last 6 months)
            days_ago = random.randint(1, 180)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            community = Community.objects.create(
                name=name,
                skill=skill,
                description=description,
                creator=creator,
                created_at=created_at
            )
            
            # Add members to the community
            # Communities have between 3 and 30 members
            potential_members = skill_users if skill_users else users
            
            # Calculate max possible members
            max_possible_members = len(potential_members)
            max_members = min(30, max_possible_members)
            min_members = min(3, max_possible_members)
            
            num_members = random.randint(min_members, max_members) if max_members >= min_members else max_possible_members
            
            # Always include the creator
            members = [creator]
            
            # Add random members
            available_members = [u for u in potential_members if u != creator]
            if available_members:
                num_to_add = min(num_members - 1, len(available_members))
                other_members = random.sample(available_members, num_to_add)
                members.extend(other_members)
            
            community.members.set(members)
            
            communities_created += 1
            print(f"Created: {name} ({len(members)} members)")
    
    print(f"\nSuccessfully created {communities_created} communities!")
    print(f"Users can now discover and join communities in the app")
    
    # Print some stats
    print("\nCommunity Statistics (Top 5 by members):")
    for community in Community.objects.annotate(num_members=models.Count('members')).order_by('-num_members')[:5]:
        print(f"  - {community.name}: {community.num_members} members")


if __name__ == '__main__':
    from django.db import models
    populate_communities()

