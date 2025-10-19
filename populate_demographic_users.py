#!/usr/bin/env python
"""
Demographic-based user population script
Creates users with specific demographics and realistic data
"""
import os
import sys
import django
from faker import Faker
import random
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ripple.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Profile, Evidence, IdentitySubmission
from skills.models import Skill, UserSkill, SkillEvidence
from django.db import transaction

# Initialize Faker with multiple locales
fake = Faker(['en_US', 'en_GB', 'en_CA', 'en_AU', 'es_ES', 'fr_FR', 'de_DE', 'it_IT', 'pt_BR'])

def create_demographic_users():
    """Create users with specific demographic profiles"""
    
    # Define demographic profiles
    demographics = [
        {
            'name': 'Tech Professionals',
            'count': 30,
            'skills': ['Python Programming', 'JavaScript Development', 'React & Redux', 'Django Web Development', 'Machine Learning', 'Data Science', 'SQL & Database Design', 'Git & Version Control', 'Docker & DevOps', 'AWS Cloud Computing'],
            'locations': ['San Francisco, CA', 'Seattle, WA', 'Austin, TX', 'New York, NY', 'Boston, MA', 'Denver, CO'],
            'bio_template': "Hi! I'm a {job} with {years} years of experience in {field}. I love working with {tech} and am always learning new technologies. Let's connect and share knowledge!",
            'jobs': ['Software Engineer', 'Data Scientist', 'DevOps Engineer', 'Product Manager', 'UX Designer', 'Full Stack Developer'],
            'fields': ['software development', 'data science', 'cloud computing', 'machine learning', 'web development'],
            'tech': ['Python', 'JavaScript', 'React', 'Django', 'AWS', 'Docker', 'Kubernetes']
        },
        {
            'name': 'Creative Professionals',
            'count': 25,
            'skills': ['UI/UX Design', 'Graphic Design', 'Digital Photography', 'Video Production', 'Adobe Creative Suite', 'Figma & Prototyping', '3D Modeling', 'Motion Graphics', 'Digital Art', 'Traditional Drawing'],
            'locations': ['Los Angeles, CA', 'New York, NY', 'Portland, OR', 'Miami, FL', 'Chicago, IL', 'Nashville, TN'],
            'bio_template': "Hello! I'm a {job} passionate about {creative_field}. I specialize in {specialty} and love creating {art_type}. Let's collaborate and inspire each other!",
            'jobs': ['Graphic Designer', 'Photographer', 'Video Editor', 'UI/UX Designer', 'Art Director', 'Creative Director'],
            'fields': ['visual design', 'photography', 'video production', 'branding', 'digital art'],
            'specialties': ['brand identity', 'web design', 'portrait photography', 'motion graphics', 'illustration'],
            'art_types': ['beautiful designs', 'compelling visuals', 'engaging content', 'memorable experiences']
        },
        {
            'name': 'Language Teachers',
            'count': 20,
            'skills': ['Spanish Language', 'French Language', 'German Language', 'Mandarin Chinese', 'Japanese Language', 'Portuguese Language', 'Italian Language', 'Russian Language', 'Public Speaking', 'Communication Skills'],
            'locations': ['Miami, FL', 'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Boston, MA', 'Seattle, WA'],
            'bio_template': "¡Hola! Bonjour! I'm a {job} with {years} years of experience teaching {language}. I'm passionate about {passion} and love helping others learn. Let's practice together!",
            'jobs': ['Language Teacher', 'ESL Instructor', 'Translator', 'Language Coach', 'Cultural Ambassador'],
            'languages': ['Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Portuguese', 'Italian', 'Russian'],
            'passions': ['cultural exchange', 'language learning', 'communication', 'travel', 'international relations']
        },
        {
            'name': 'Wellness Professionals',
            'count': 15,
            'skills': ['Personal Training', 'Yoga Instruction', 'Meditation & Mindfulness', 'Nutrition Coaching', 'Life Coaching', 'Mental Health Support', 'Fitness Training', 'Wellness Coaching'],
            'locations': ['Boulder, CO', 'Portland, OR', 'Austin, TX', 'San Diego, CA', 'Asheville, NC', 'Santa Fe, NM'],
            'bio_template': "Namaste! I'm a {job} dedicated to helping others achieve {wellness_goal}. I specialize in {specialty} and believe in {philosophy}. Let's work together on your wellness journey!",
            'jobs': ['Personal Trainer', 'Yoga Instructor', 'Nutritionist', 'Life Coach', 'Wellness Coach', 'Meditation Teacher'],
            'goals': ['optimal health', 'mental wellness', 'physical fitness', 'life balance', 'inner peace'],
            'specialties': ['strength training', 'mindfulness', 'nutrition planning', 'stress management', 'holistic wellness'],
            'philosophies': ['holistic health', 'mind-body connection', 'sustainable wellness', 'personal growth']
        },
        {
            'name': 'Business Professionals',
            'count': 20,
            'skills': ['Project Management', 'Public Speaking', 'Business Strategy', 'Sales & Negotiation', 'Financial Analysis', 'HR & Recruitment', 'Leadership Development', 'Digital Marketing'],
            'locations': ['New York, NY', 'Chicago, IL', 'Houston, TX', 'Atlanta, GA', 'Dallas, TX', 'Phoenix, AZ'],
            'bio_template': "Hello! I'm a {job} with expertise in {business_area}. I've helped {achievement} and am passionate about {passion}. Let's network and grow together!",
            'jobs': ['Business Consultant', 'Project Manager', 'Sales Director', 'Marketing Manager', 'HR Manager', 'Financial Analyst'],
            'areas': ['strategic planning', 'team leadership', 'process improvement', 'market analysis', 'client relations'],
            'achievements': ['companies scale their operations', 'teams achieve their goals', 'organizations improve efficiency', 'businesses increase revenue'],
            'passions': ['business growth', 'team development', 'strategic thinking', 'innovation', 'leadership']
        },
        {
            'name': 'Arts & Music',
            'count': 15,
            'skills': ['Guitar Performance', 'Piano & Keyboard', 'Music Production', 'Digital Art', 'Traditional Drawing', 'Painting Techniques', 'Sculpture', 'Creative Writing'],
            'locations': ['Nashville, TN', 'Austin, TX', 'Portland, OR', 'Seattle, WA', 'New Orleans, LA', 'San Francisco, CA'],
            'bio_template': "Hey there! I'm a {job} who loves {art_form}. I've been {activity} for {years} years and enjoy {enjoyment}. Let's create something amazing together!",
            'jobs': ['Musician', 'Artist', 'Writer', 'Music Producer', 'Painter', 'Sculptor'],
            'forms': ['creating music', 'making art', 'writing stories', 'producing beats', 'painting'],
            'activities': ['playing music', 'creating art', 'writing', 'producing', 'painting'],
            'enjoyments': ['collaborating with other artists', 'teaching my craft', 'sharing my passion', 'inspiring others']
        }
    ]
    
    # Create skills first
    all_skills = create_comprehensive_skills()
    
    users_created = []
    
    for demo in demographics:
        print(f"Creating {demo['count']} {demo['name']}...")
        demo_users = create_demographic_group(demo, all_skills)
        users_created.extend(demo_users)
    
    # Create some cross-demographic matches
    create_diverse_matches(users_created, all_skills)
    
    return users_created, all_skills

def create_comprehensive_skills():
    """Create all skills needed for demographic groups"""
    skills_data = [
        # Technology
        'Python Programming', 'JavaScript Development', 'React & Redux', 'Django Web Development', 'Node.js & Express',
        'Machine Learning', 'Data Science', 'SQL & Database Design', 'Git & Version Control', 'Docker & DevOps',
        'AWS Cloud Computing', 'Cybersecurity',
        
        # Design & Creative
        'UI/UX Design', 'Graphic Design', 'Digital Photography', 'Video Production', 'Adobe Creative Suite',
        'Figma & Prototyping', '3D Modeling', 'Motion Graphics', 'Digital Art', 'Traditional Drawing',
        
        # Business & Marketing
        'Digital Marketing', 'Content Marketing', 'Project Management', 'Public Speaking', 'Business Strategy',
        'Sales & Negotiation', 'Financial Analysis', 'HR & Recruitment', 'Leadership Development',
        
        # Languages
        'Spanish Language', 'French Language', 'German Language', 'Mandarin Chinese', 'Japanese Language',
        'Portuguese Language', 'Italian Language', 'Russian Language',
        
        # Arts & Music
        'Guitar Performance', 'Piano & Keyboard', 'Music Production', 'Digital Art', 'Traditional Drawing',
        'Painting Techniques', 'Sculpture', 'Creative Writing',
        
        # Lifestyle & Wellness
        'Professional Cooking', 'Artisan Baking', 'Personal Training', 'Yoga Instruction', 'Meditation & Mindfulness',
        'Nutrition Coaching', 'Life Coaching', 'Mental Health Support',
        
        # Professional Skills
        'Excel & Data Analysis', 'PowerPoint Design', 'Leadership Development', 'Conflict Resolution',
        'Time Management', 'Critical Thinking', 'Communication Skills', 'Networking & Relationship Building'
    ]
    
    skills = []
    for skill_name in skills_data:
        skill, created = Skill.objects.get_or_create(
            name=skill_name,
            defaults={'description': f'Learn {skill_name} from experienced professionals'}
        )
        skills.append(skill)
    
    return skills

def create_demographic_group(demo, all_skills):
    """Create users for a specific demographic group"""
    users = []
    
    with transaction.atomic():
        for i in range(demo['count']):
            # Generate realistic data based on demographic
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            
            # Generate email
            email_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
            email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(email_domains)}"
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password='demo123',
                first_name=first_name,
                last_name=last_name,
                date_joined=fake.date_time_between(start_date='-2y', end_date='now')
            )
            
            # Create profile with demographic-specific data
            profile = Profile.objects.get(user=user)
            profile.bio = generate_demographic_bio(demo, fake)
            profile.location = random.choice(demo['locations'])
            profile.verification_status = random.choices(['verified', 'pending', 'unverified'], weights=[60, 20, 20])[0]
            profile.save()
            
            # Create identity submission for verified users
            if profile.verification_status == 'verified':
                IdentitySubmission.objects.create(
                    profile=profile,
                    first_name=first_name,
                    last_name=last_name,
                    dob=fake.date_of_birth(minimum_age=22, maximum_age=55),
                    nationality=fake.country(),
                    address1=fake.street_address(),
                    address2=fake.secondary_address() if fake.boolean() else '',
                    state=fake.state(),
                    postal=fake.postcode(),
                    country=fake.country()
                )
            
            # Assign demographic-specific skills
            assign_demographic_skills(user, demo, all_skills)
            
            users.append(user)
            print(f"  Created {demo['name']}: {user.username} ({user.email})")
    
    return users

def generate_demographic_bio(demo, fake):
    """Generate bio based on demographic profile"""
    if demo['name'] == 'Tech Professionals':
        job = random.choice(demo['jobs'])
        years = random.randint(2, 10)
        field = random.choice(demo['fields'])
        tech = random.choice(demo['tech'])
        return demo['bio_template'].format(job=job, years=years, field=field, tech=tech)
    
    elif demo['name'] == 'Creative Professionals':
        job = random.choice(demo['jobs'])
        creative_field = random.choice(demo['fields'])
        specialty = random.choice(demo['specialties'])
        art_type = random.choice(demo['art_types'])
        return demo['bio_template'].format(job=job, creative_field=creative_field, specialty=specialty, art_type=art_type)
    
    elif demo['name'] == 'Language Teachers':
        job = random.choice(demo['jobs'])
        years = random.randint(1, 15)
        language = random.choice(demo['languages'])
        passion = random.choice(demo['passions'])
        return demo['bio_template'].format(job=job, years=years, language=language, passion=passion)
    
    elif demo['name'] == 'Wellness Professionals':
        job = random.choice(demo['jobs'])
        wellness_goal = random.choice(demo['goals'])
        specialty = random.choice(demo['specialties'])
        philosophy = random.choice(demo['philosophies'])
        return demo['bio_template'].format(job=job, wellness_goal=wellness_goal, specialty=specialty, philosophy=philosophy)
    
    elif demo['name'] == 'Business Professionals':
        job = random.choice(demo['jobs'])
        business_area = random.choice(demo['areas'])
        achievement = random.choice(demo['achievements'])
        passion = random.choice(demo['passions'])
        return demo['bio_template'].format(job=job, business_area=business_area, achievement=achievement, passion=passion)
    
    elif demo['name'] == 'Arts & Music':
        job = random.choice(demo['jobs'])
        art_form = random.choice(demo['forms'])
        activity = random.choice(demo['activities'])
        years = random.randint(3, 20)
        enjoyment = random.choice(demo['enjoyments'])
        return demo['bio_template'].format(job=job, art_form=art_form, activity=activity, years=years, enjoyment=enjoyment)
    
    else:
        return f"Hi! I'm {fake.first_name()}, excited to be part of this learning community!"

def assign_demographic_skills(user, demo, all_skills):
    """Assign skills based on demographic profile"""
    # Get skills that match this demographic
    demo_skill_names = demo['skills']
    demo_skills = [skill for skill in all_skills if skill.name in demo_skill_names]
    
    # Each user gets 3-6 skills from their demographic
    num_skills = random.randint(3, 6)
    user_skills = random.sample(demo_skills, min(num_skills, len(demo_skills)))
    
    skill_levels = ['beginner', 'intermediate', 'advanced', 'expert']
    
    for skill in user_skills:
        level = random.choices(skill_levels, weights=[20, 50, 25, 5])[0]
        can_teach = random.choices([True, False], weights=[70, 30])[0]  # Higher chance for demographic skills
        wants_to_learn = random.choices([True, False], weights=[60, 40])[0]
        
        # Ensure at least one teaching skill
        if skill == user_skills[0]:
            can_teach = True
        
        user_skill, created = UserSkill.objects.get_or_create(
            user=user,
            skill=skill,
            defaults={
                'level': level,
                'can_teach': can_teach,
                'wants_to_learn': wants_to_learn,
                'verification_status': random.choices(['verified', 'pending', 'unverified'], weights=[50, 20, 30])[0]
            }
        )
        
        # Add evidence for teaching skills
        if user_skill.can_teach and random.random() < 0.6:
            create_demographic_evidence(user_skill, demo)

def create_demographic_evidence(user_skill, demo):
    """Create evidence based on demographic"""
    if demo['name'] == 'Tech Professionals':
        portfolio_domains = ['github.com', 'linkedin.com', 'dev.to', 'stackoverflow.com']
        link = f"https://{random.choice(portfolio_domains)}/{user_skill.user.username}"
        title = f"{user_skill.skill.name} Portfolio"
        description = f"Check out my {user_skill.skill.name} projects and contributions"
    
    elif demo['name'] == 'Creative Professionals':
        portfolio_domains = ['behance.net', 'dribbble.com', 'portfolio.com', 'carrd.co']
        link = f"https://{random.choice(portfolio_domains)}/{user_skill.user.username}"
        title = f"{user_skill.skill.name} Showcase"
        description = f"View my creative work in {user_skill.skill.name}"
    
    else:
        link = f"https://portfolio.com/{user_skill.user.username}"
        title = f"{user_skill.skill.name} Experience"
        description = f"Learn more about my {user_skill.skill.name} background"
    
    SkillEvidence.objects.get_or_create(
        user_skill=user_skill,
        title=title,
        defaults={
            'evidence_type': 'link',
            'link': link,
            'description': description,
            'is_primary': True
        }
    )

def create_diverse_matches(users, skills):
    """Create matches between different demographic groups"""
    from skills.models import Match
    
    print("Creating diverse matches...")
    matches_created = 0
    
    # Create 30-60 cross-demographic matches
    num_matches = random.randint(30, 60)
    
    for _ in range(num_matches):
        user_a = random.choice(users)
        user_b = random.choice(users)
        
        if user_a == user_b:
            continue
        
        # Find compatible skills
        user_a_teaching = UserSkill.objects.filter(user=user_a, can_teach=True).values_list('skill', flat=True)
        user_b_learning = UserSkill.objects.filter(user=user_b, wants_to_learn=True).values_list('skill', flat=True)
        user_b_teaching = UserSkill.objects.filter(user=user_b, can_teach=True).values_list('skill', flat=True)
        user_a_learning = UserSkill.objects.filter(user=user_a, wants_to_learn=True).values_list('skill', flat=True)
        
        # Check for potential matches
        teach_a_learn_b = set(user_a_teaching) & set(user_b_learning)
        teach_b_learn_a = set(user_b_teaching) & set(user_a_learning)
        
        if teach_a_learn_b and teach_b_learn_a:
            skill_a_id = random.choice(list(teach_a_learn_b))
            skill_b_id = random.choice(list(teach_b_learn_a))
            
            skill_a = Skill.objects.get(id=skill_a_id)
            skill_b = Skill.objects.get(id=skill_b_id)
            
            match, created = Match.objects.get_or_create(
                user_a=user_a,
                user_b=user_b,
                teach_a_learn_b=skill_a,
                teach_b_learn_a=skill_b
            )
            
            if created:
                matches_created += 1
    
    print(f"Created {matches_created} diverse matches")

def main():
    """Main function"""
    print("🎯 Starting demographic user population...")
    
    users, skills = create_demographic_users()
    
    print(f"\n✅ Successfully created {len(users)} demographic users with {len(skills)} skills!")
    print("\n📋 Sample login credentials:")
    print("Username: [firstname][lastname][number] (e.g., johnsmith123)")
    print("Password: demo123")
    
    print(f"\n📊 Demographics created:")
    print("- 30 Tech Professionals")
    print("- 25 Creative Professionals") 
    print("- 20 Language Teachers")
    print("- 15 Wellness Professionals")
    print("- 20 Business Professionals")
    print("- 15 Arts & Music Professionals")
    
    print(f"\n🔍 Sample users:")
    for user in users[:10]:
        print(f"- {user.username} ({user.email}) - {user.first_name} {user.last_name}")

if __name__ == '__main__':
    main()
