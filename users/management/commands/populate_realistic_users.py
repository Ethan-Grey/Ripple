"""
Django management command to populate the database with realistic users
Uses Faker library to generate authentic-looking data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from users.models import Profile, Evidence, IdentitySubmission
from skills.models import Skill, UserSkill, SkillEvidence, Match
from faker import Faker
import random
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Populate the database with realistic users using Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of users to create (default: 100)'
        )
        parser.add_argument(
            '--locale',
            type=str,
            default='en_US',
            help='Faker locale (default: en_US)'
        )
        parser.add_argument(
            '--verified-ratio',
            type=float,
            default=0.3,
            help='Ratio of verified users (default: 0.3)'
        )

    def handle(self, *args, **options):
        user_count = options['count']
        locale = options['locale']
        verified_ratio = options['verified_ratio']
        
        # Initialize Faker with specified locale
        fake = Faker(locale)
        
        self.stdout.write(f'Creating {user_count} realistic users...')
        
        # Create skills first
        skills = self.create_realistic_skills()
        
        # Create users
        users = self.create_realistic_users(fake, user_count, verified_ratio)
        
        # Assign skills
        self.assign_realistic_skills(fake, users, skills)
        
        # Create matches
        self.create_realistic_matches(users, skills)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(users)} realistic users with {len(skills)} skills!'
            )
        )

    def create_realistic_skills(self):
        """Create comprehensive skill set"""
        skills_data = [
            # Technology
            {'name': 'Python Programming', 'description': 'Master Python for web development, data science, and automation'},
            {'name': 'JavaScript Development', 'description': 'Modern JavaScript, ES6+, and frontend frameworks'},
            {'name': 'React & Redux', 'description': 'Build dynamic user interfaces with React ecosystem'},
            {'name': 'Django Web Development', 'description': 'Create robust web applications with Django'},
            {'name': 'Node.js & Express', 'description': 'Server-side JavaScript development'},
            {'name': 'Machine Learning', 'description': 'AI and ML with Python, TensorFlow, and scikit-learn'},
            {'name': 'Data Science', 'description': 'Data analysis with Python, R, and statistical methods'},
            {'name': 'SQL & Database Design', 'description': 'Database design and optimization'},
            {'name': 'Git & Version Control', 'description': 'Collaborative development workflows'},
            {'name': 'Docker & DevOps', 'description': 'Containerization and cloud deployment'},
            {'name': 'AWS Cloud Computing', 'description': 'Amazon Web Services and cloud architecture'},
            {'name': 'Cybersecurity', 'description': 'Information security and ethical hacking'},
            
            # Design & Creative
            {'name': 'UI/UX Design', 'description': 'User interface and experience design'},
            {'name': 'Graphic Design', 'description': 'Visual communications and branding'},
            {'name': 'Digital Photography', 'description': 'Professional photography and editing'},
            {'name': 'Video Production', 'description': 'Video editing and post-production'},
            {'name': 'Adobe Creative Suite', 'description': 'Photoshop, Illustrator, and design tools'},
            {'name': 'Figma & Prototyping', 'description': 'Collaborative design and prototyping'},
            {'name': '3D Modeling', 'description': '3D design with Blender, Maya, or Cinema 4D'},
            {'name': 'Motion Graphics', 'description': 'Animation and motion design'},
            
            # Business & Marketing
            {'name': 'Digital Marketing', 'description': 'SEO, social media, and online advertising'},
            {'name': 'Content Marketing', 'description': 'Content strategy and creation'},
            {'name': 'Project Management', 'description': 'Agile, Scrum, and team leadership'},
            {'name': 'Public Speaking', 'description': 'Presentation and communication skills'},
            {'name': 'Business Strategy', 'description': 'Strategic planning and development'},
            {'name': 'Sales & Negotiation', 'description': 'Sales techniques and client relations'},
            {'name': 'Financial Analysis', 'description': 'Financial modeling and investment analysis'},
            {'name': 'HR & Recruitment', 'description': 'Human resources and talent acquisition'},
            
            # Languages
            {'name': 'Spanish Language', 'description': 'Spanish for business and cultural exchange'},
            {'name': 'French Language', 'description': 'French conversation and cultural nuances'},
            {'name': 'German Language', 'description': 'German for business and travel'},
            {'name': 'Mandarin Chinese', 'description': 'Chinese language for global business'},
            {'name': 'Japanese Language', 'description': 'Japanese language and culture'},
            {'name': 'Portuguese Language', 'description': 'Portuguese for business and travel'},
            {'name': 'Italian Language', 'description': 'Italian language and culture'},
            {'name': 'Russian Language', 'description': 'Russian language and literature'},
            
            # Arts & Music
            {'name': 'Guitar Performance', 'description': 'Acoustic and electric guitar techniques'},
            {'name': 'Piano & Keyboard', 'description': 'Classical and contemporary piano'},
            {'name': 'Music Production', 'description': 'Digital audio workstations and mixing'},
            {'name': 'Digital Art', 'description': 'Digital painting and illustration'},
            {'name': 'Traditional Drawing', 'description': 'Pencil, charcoal, and ink drawing'},
            {'name': 'Painting Techniques', 'description': 'Watercolor, oil, and acrylic painting'},
            {'name': 'Sculpture', 'description': '3D art and sculpture techniques'},
            {'name': 'Creative Writing', 'description': 'Fiction, poetry, and creative storytelling'},
            
            # Lifestyle & Wellness
            {'name': 'Professional Cooking', 'description': 'Culinary techniques and international cuisine'},
            {'name': 'Artisan Baking', 'description': 'Bread, pastries, and dessert creation'},
            {'name': 'Personal Training', 'description': 'Fitness training and exercise science'},
            {'name': 'Yoga Instruction', 'description': 'Yoga practice and teaching methods'},
            {'name': 'Meditation & Mindfulness', 'description': 'Meditation techniques and wellness'},
            {'name': 'Nutrition Coaching', 'description': 'Healthy eating and meal planning'},
            {'name': 'Life Coaching', 'description': 'Personal development and goal setting'},
            {'name': 'Mental Health Support', 'description': 'Counseling and mental wellness'},
            
            # Professional Skills
            {'name': 'Excel & Data Analysis', 'description': 'Advanced Excel and data visualization'},
            {'name': 'PowerPoint Design', 'description': 'Professional presentations and storytelling'},
            {'name': 'Leadership Development', 'description': 'Team leadership and management'},
            {'name': 'Conflict Resolution', 'description': 'Mediation and problem-solving skills'},
            {'name': 'Time Management', 'description': 'Productivity and organization techniques'},
            {'name': 'Critical Thinking', 'description': 'Analytical reasoning and problem-solving'},
            {'name': 'Communication Skills', 'description': 'Written and verbal communication'},
            {'name': 'Networking & Relationship Building', 'description': 'Professional networking strategies'},
        ]
        
        skills = []
        for skill_data in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults={'description': skill_data['description']}
            )
            skills.append(skill)
            
        return skills

    def create_realistic_users(self, fake, count, verified_ratio):
        """Create users with realistic data"""
        users = []
        
        with transaction.atomic():
            for i in range(count):
                # Generate realistic personal data
                first_name = fake.first_name()
                last_name = fake.last_name()
                username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
                
                # Generate realistic email
                email_domains = [
                    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com',
                    'protonmail.com', 'fastmail.com', 'zoho.com', 'mail.com', 'yandex.com',
                    'aol.com', 'live.com', 'msn.com', 'comcast.net', 'verizon.net'
                ]
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
                
                # Create profile with realistic data
                profile = Profile.objects.get(user=user)
                profile.bio = self.generate_realistic_bio(fake)
                profile.location = f"{fake.city()}, {fake.state_abbr()}"
                profile.verification_status = 'verified' if random.random() < verified_ratio else 'unverified'
                profile.save()
                
                # Create identity submission for verified users
                if profile.verification_status == 'verified':
                    IdentitySubmission.objects.create(
                        profile=profile,
                        first_name=first_name,
                        last_name=last_name,
                        dob=fake.date_of_birth(minimum_age=18, maximum_age=65),
                        nationality=fake.country(),
                        address1=fake.street_address(),
                        address2=fake.secondary_address() if fake.boolean() else '',
                        state=fake.state(),
                        postal=fake.postcode(),
                        country=fake.country()
                    )
                
                users.append(user)
                
        return users

    def generate_realistic_bio(self, fake):
        """Generate realistic user bio"""
        bio_templates = [
            f"Hi! I'm {fake.first_name()}, a passionate professional with {random.randint(2, 10)} years of experience. I love learning new skills and sharing knowledge with others. When I'm not working, you can find me {fake.catch_phrase().lower()}.",
            f"Hello! I'm {fake.first_name()}, originally from {fake.city()}. I'm excited to be part of this community where we can all learn and grow together. My interests include {fake.word()}, {fake.word()}, and {fake.word()}.",
            f"Hey there! I'm {fake.first_name()}, a {fake.job()} based in {fake.city()}. I believe in the power of continuous learning and am always looking for new challenges. Let's connect and learn from each other!",
            f"Hi everyone! I'm {fake.first_name()}, and I'm passionate about {fake.word()} and {fake.word()}. I've been {fake.catch_phrase().lower()} for the past few years and love helping others develop their skills.",
            f"Hello! I'm {fake.first_name()}, a {fake.job()} with a love for teaching and learning. I'm originally from {fake.country()} but now live in {fake.city()}. Excited to share knowledge with this amazing community!"
        ]
        
        return random.choice(bio_templates)

    def assign_realistic_skills(self, fake, users, skills):
        """Assign realistic skills to users"""
        skill_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        
        for user in users:
            # Each user gets 2-8 skills
            num_skills = random.randint(2, 8)
            user_skills = random.sample(skills, num_skills)
            
            for skill in user_skills:
                level = random.choices(
                    skill_levels,
                    weights=[25, 45, 25, 5]  # Most users are intermediate
                )[0]
                
                can_teach = random.choices([True, False], weights=[55, 45])[0]
                wants_to_learn = random.choices([True, False], weights=[70, 30])[0]
                
                # Ensure at least one teaching or learning skill
                if skill == user_skills[0]:
                    can_teach = True
                elif skill == user_skills[1]:
                    wants_to_learn = True
                
                user_skill, created = UserSkill.objects.get_or_create(
                    user=user,
                    skill=skill,
                    defaults={
                        'level': level,
                        'can_teach': can_teach,
                        'wants_to_learn': wants_to_learn,
                        'verification_status': random.choices(
                            ['unverified', 'pending', 'verified'],
                            weights=[50, 20, 30]
                        )[0]
                    }
                )
                
                # Add realistic evidence for teaching skills
                if user_skill.can_teach and random.random() < 0.5:  # 50% chance
                    self.create_realistic_evidence(fake, user_skill)

    def create_realistic_evidence(self, fake, user_skill):
        """Create realistic evidence for skills"""
        evidence_types = ['link', 'document', 'image']
        evidence_type = random.choice(evidence_types)
        
        if evidence_type == 'link':
            portfolio_domains = [
                'github.com', 'behance.net', 'dribbble.com', 'codepen.io',
                'linkedin.com', 'medium.com', 'dev.to', 'stackoverflow.com',
                'portfolio.com', 'carrd.co', 'notion.site', 'wix.com'
            ]
            link = f"https://{random.choice(portfolio_domains)}/{user_skill.user.username}"
            title = f"My {user_skill.skill.name} Portfolio"
            description = f"Check out my work and projects in {user_skill.skill.name}. I've been working with this technology for {random.randint(1, 5)} years."
        else:
            link = ''
            title = f"{user_skill.skill.name} Certification"
            description = f"Certificate and documentation demonstrating my expertise in {user_skill.skill.name}"
        
        SkillEvidence.objects.get_or_create(
            user_skill=user_skill,
            title=title,
            defaults={
                'evidence_type': evidence_type,
                'link': link,
                'description': description,
                'is_primary': True
            }
        )

    def create_realistic_matches(self, users, skills):
        """Create realistic matches between users"""
        matches_created = 0
        num_matches = random.randint(20, 50)
        
        for _ in range(num_matches):
            user_a = random.choice(users)
            user_b = random.choice(users)
            
            if user_a == user_b:
                continue
                
            # Find compatible skills
            user_a_teaching = UserSkill.objects.filter(
                user=user_a, can_teach=True
            ).values_list('skill', flat=True)
            
            user_b_learning = UserSkill.objects.filter(
                user=user_b, wants_to_learn=True
            ).values_list('skill', flat=True)
            
            user_b_teaching = UserSkill.objects.filter(
                user=user_b, can_teach=True
            ).values_list('skill', flat=True)
            
            user_a_learning = UserSkill.objects.filter(
                user=user_a, wants_to_learn=True
            ).values_list('skill', flat=True)
            
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
        
        self.stdout.write(f'Created {matches_created} realistic matches between users')
