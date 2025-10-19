# Realistic User Population Guide

This guide explains how to populate your Ripple website with realistic, authentic-looking user data for development and testing purposes.

## Overview

The realistic user population system creates users with:
- **Realistic names** from diverse backgrounds
- **Authentic email addresses** based on names
- **Real-world locations** (cities and states)
- **Professional bios** that sound genuine
- **Diverse skill sets** matching professional demographics
- **Verified skills** with evidence
- **Active matches** between users

## Methods to Populate Users

### Method 1: Django Management Command (Recommended)

The easiest and most integrated way to populate users.

#### Usage:

```bash
# Activate virtual environment first
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source venv/bin/activate  # Mac/Linux

# Populate users (default: 50 users)
python manage.py populate_realistic_users

# Populate specific number of users
python manage.py populate_realistic_users 100
```

#### What it creates:
- **Users**: Realistic profiles with diverse names and locations
- **Skills**: 50+ common skills across various domains
- **User Skills**: Each user gets 2-5 teaching skills and 1-3 learning goals
- **Verified Skills**: Random skills are verified with evidence
- **Matches**: Creates skill exchange matches between compatible users
- **Profiles**: Complete profiles with bios, locations, and verification status

#### Location: `users/management/commands/populate_realistic_users.py`

---

### Method 2: Standalone Python Scripts

Alternative scripts that can be run directly for specific use cases.

#### Script 1: Basic Realistic Users
**Location**: `scripts/populate_realistic.py`

Creates users with realistic data but simpler implementation.

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the script
python scripts/populate_realistic.py
```

**Prompts you for:**
- Number of users to create
- Creates users with names, emails, addresses, bios

#### Script 2: Demographic-Based Users
**Location**: `scripts/populate_demographic_users.py`

Creates users across specific professional demographics with tailored skills.

```bash
python scripts/populate_demographic_users.py
```

**Creates users in categories:**
- Software Engineers (Bay Area)
- Healthcare Workers (New York)
- Teachers (Chicago)
- Artists & Designers (Austin)
- Business Professionals (Boston)
- Trades & Crafts (Denver)

---

## Default Password

All generated users have the same password for easy testing:

**Password**: `testpass123`

You can log in with any generated username and this password.

---

## Data Characteristics

### Names
- Diverse first and last names from various cultural backgrounds
- Realistic combinations (e.g., "Sarah Johnson", "Marcus Chen", "Aisha Patel")

### Emails
- Based on user's name (e.g., `sarah.johnson@example.com`)
- Multiple domain variations (@gmail.com, @yahoo.com, @outlook.com, etc.)

### Locations
- Real US cities with proper state names
- Variety across different regions

### Bios
- Professional-sounding descriptions
- Industry-specific language
- Varied lengths and styles

### Skills
Covers multiple domains:
- **Tech**: Python, JavaScript, Web Development, Data Science
- **Creative**: Graphic Design, Photography, Video Editing
- **Business**: Marketing, Project Management, Accounting
- **Languages**: Spanish, French, Mandarin
- **Trades**: Carpentry, Plumbing, Electrical Work
- **Wellness**: Yoga, Meditation, Fitness Training
- **Academic**: Math Tutoring, Writing, Music Theory

### Verification Status
- ~30% of users are verified
- Verified users have identity submissions approved
- Some skills are verified with evidence

---

## Step-by-Step: Getting Started

### 1. **Ensure Virtual Environment is Active**
```bash
.\venv\Scripts\Activate.ps1  # Windows
```

### 2. **Run Migrations** (if needed)
```bash
python manage.py migrate
```

### 3. **Populate Users**
```bash
python manage.py populate_realistic_users 50
```

### 4. **Start the Server**
```bash
python manage.py runserver
```

### 5. **Explore the Data**
- Go to `/search/` and search for users
- Try different name searches
- View user profiles
- Log in as test users (password: `testpass123`)

---

## Viewing Generated Data

### In Django Admin
```bash
# Create superuser if you haven't
python manage.py createsuperuser

# Access admin at http://localhost:8000/admin/
```

### In Django Shell
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from users.models import Profile
from skills.models import Skill, UserSkill

# View user count
User.objects.count()

# View users with verified profiles
Profile.objects.filter(verification_status='verified').count()

# View skills
Skill.objects.all()

# View user skills
UserSkill.objects.filter(can_teach=True).count()
```

---

## Customization

### Change Default Password

Edit the management command or script and change:
```python
user.set_password('testpass123')  # Change this
```

### Adjust User Demographics

Modify the demographic distributions in:
- `users/management/commands/populate_realistic_users.py`
- `scripts/populate_demographic_users.py`

### Add More Skills

Edit the `SKILLS` list in the population scripts to add domain-specific skills.

---

## Troubleshooting

### Issue: "Faker is not installed"
```bash
pip install Faker
```

### Issue: "Duplicate username/email"
The scripts check for existing users and skip duplicates. If you see warnings, it's normal.

### Issue: "No module named users.management"
Make sure you're in the project root directory when running commands.

### Issue: Unicode errors in console
The scripts should handle this automatically, but if you see encoding errors, they're just display issues and don't affect data creation.

---

## Clean Up

To remove all test data:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from skills.models import Skill, UserSkill, Match

# Delete all non-superuser users
User.objects.filter(is_superuser=False).delete()

# Or delete everything (careful!)
UserSkill.objects.all().delete()
Match.objects.all().delete()
Skill.objects.all().delete()
```

---

## Best Practices

1. **Development Only**: This is for development/testing, not production
2. **Consistent Password**: Keep the same password for all test users for easy testing
3. **Reasonable Numbers**: Start with 20-50 users, increase as needed
4. **Database Backups**: Backup your database before large operations
5. **Re-run Safely**: Scripts check for duplicates, so safe to re-run

---

## Next Steps

After populating users:
1. **Test Search**: Try searching for users by name or location
2. **View Profiles**: Click on users to see their detailed profiles
3. **Test Messaging**: Send messages between users
4. **Test Matching**: View skill exchange matches
5. **Test Verification**: Review the verification system with verified users

---

## Files Reference

- **Management Command**: `users/management/commands/populate_realistic_users.py`
- **Script 1**: `scripts/populate_realistic.py`
- **Script 2**: `scripts/populate_demographic_users.py`
- **Dependencies**: Listed in `requirements.txt` (includes Faker)

---

**Happy Testing! 🚀**

For questions or issues, check the script comments or review the console output for detailed progress information.

