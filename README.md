# Ripple - Skill-Sharing Platform

Ripple is a comprehensive skill-sharing platform that connects learners and teachers, enabling knowledge exchange through classes, communities, and skill trading. Built with Django and modern web technologies, Ripple provides a seamless experience for users to teach, learn, and grow together.

## 🌟 Features

### Core Functionality

- **Teaching Classes**: Users can apply to become teachers and create online classes
- **Learning Platform**: Browse, enroll, and learn from expert-led courses
- **Skill Trading**: Trade classes with other users for mutual learning
- **Communities**: Join skill-based communities to connect and share resources
- **Messaging System**: Real-time chat functionality for user communication
- **Skill Verification**: Get verified for your skills with evidence submission
- **User Profiles**: Comprehensive profiles showcasing skills, classes, and achievements
- **Payment Integration**: Stripe integration for class enrollment payments
- **Admin Dashboard**: Full admin panel for managing users, classes, and communities

### Key Capabilities

- **Class Management**: Create, edit, schedule, and manage teaching classes
- **Booking System**: Schedule and manage class sessions with time slots
- **Community Features**: Post discussions, share resources, and interact with members
- **Search & Discovery**: Advanced filtering and search for classes and communities
- **User Verification**: Identity and skill verification system
- **Trade Offers**: Propose and manage class trades between users
- **Favorites**: Save favorite classes for easy access
- **Reviews & Ratings**: Rate and review classes

## 🛠️ Technology Stack

### Backend
- **Django 5.2.7**: Python web framework
- **PostgreSQL**: Production database (via `psycopg2-binary`)
- **SQLite**: Development database
- **Django Allauth**: Authentication and user management
- **Stripe**: Payment processing
- **SendGrid**: Email delivery

### Frontend
- **HTML5/CSS3**: Modern, responsive design
- **JavaScript/React**: Interactive components and dynamic rendering
- **Bootstrap 5**: UI framework
- **AOS (Animate On Scroll)**: Scroll animations
- **Tailwind CSS**: Utility-first CSS framework

### Deployment
- **Gunicorn**: WSGI HTTP server
- **WhiteNoise**: Static file serving
- **Railway/Render**: Cloud hosting platforms

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **pip**: Python package manager (comes with Python)
- **PostgreSQL** (for production) or **SQLite** (for development)
- **Git**: [Download Git](https://git-scm.com/downloads)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Ripple
```

### 2. Create a Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root (use `ENV_TEMPLATE.txt` as a reference):

```bash
cp ENV_TEMPLATE.txt .env
```

Edit `.env` and configure the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Development - SQLite)
# For production, configure PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/ripple

# Email Configuration (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@ripple.com

# Stripe Configuration
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Media Files
MEDIA_ROOT=media
STATIC_ROOT=staticfiles
```

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create a superuser (admin account)
python manage.py createsuperuser
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## 📁 Project Structure

```
Ripple/
├── chat/                 # Messaging system
│   ├── models.py        # Conversation and message models
│   ├── views.py         # Chat views and logic
│   └── templates/       # Chat templates
│
├── communities/         # Community features
│   ├── models.py        # Community and post models
│   ├── views.py         # Community views
│   └── templates/       # Community templates
│
├── core/                # Core application features
│   ├── models.py        # Core models (reports, etc.)
│   ├── views.py         # Dashboard, landing, search
│   └── templates/       # Core templates
│
├── ripple/              # Main project settings
│   ├── settings.py      # Django settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI configuration
│
├── skills/              # Classes and teaching features
│   ├── models.py        # TeachingClass, TeacherApplication models
│   ├── views.py         # Class views and checkout
│   ├── templates/       # Class templates
│   └── management/      # Management commands
│
├── skill_admin/         # Skill administration
│   └── views.py         # Skill review and admin views
│
├── users/               # User management
│   ├── models.py        # User profiles and skills
│   ├── views.py         # Authentication and profiles
│   ├── templates/       # User templates
│   └── management/     # User population commands
│
├── static/              # Static files (CSS, JS, images)
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
│
├── templates/           # Base templates
│   └── base.html        # Main base template
│
├── media/               # User-uploaded files
│   ├── avatars/         # User profile pictures
│   ├── class_thumbs/    # Class thumbnails
│   └── ...
│
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
├── Procfile             # Deployment configuration
└── README.md           # This file
```

## 🔧 Configuration

### Database Configuration

**Development (SQLite):**
No additional configuration needed. SQLite is used by default.

**Production (PostgreSQL):**
```env
DATABASE_URL=postgresql://username:password@host:port/database_name
```

### Email Configuration

Configure SendGrid in your `.env` file:
```env
SENDGRID_API_KEY=your-api-key
DEFAULT_FROM_EMAIL=your-email@domain.com
```

### Stripe Configuration

1. Create a Stripe account at [stripe.com](https://stripe.com)
2. Get your API keys from the Stripe Dashboard
3. Configure webhook endpoint: `https://yourdomain.com/webhooks/stripe/`
4. Add webhook events: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded`, `charge.dispute.created`
5. Add keys to `.env`:
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 📖 Usage Guide

### For Administrators

1. **Access Admin Panel**: Navigate to `/admin/` and log in with superuser credentials
2. **Manage Users**: Review and verify user identities and skills
3. **Review Applications**: Approve or reject teacher applications
4. **Manage Classes**: Review, approve, and manage teaching classes
5. **Community Management**: Approve community requests and moderate content

### For Teachers

1. **Verify Identity**: Complete identity verification in your profile
2. **Apply to Teach**: Submit a teaching application with class details
3. **Create Classes**: Once approved, create and publish your classes
4. **Manage Schedule**: Set up available time slots for sessions
5. **Engage with Students**: Respond to bookings and complete sessions

### For Learners

1. **Browse Classes**: Explore available classes on the classes page
2. **Enroll in Classes**: Purchase or trade for class access
3. **Book Sessions**: Schedule one-on-one sessions with teachers
4. **Join Communities**: Connect with others learning the same skills
5. **Track Progress**: View your enrolled classes and upcoming sessions

## 🧪 Testing

### Run Tests

```bash
python manage.py test
```

### Populate Test Data

Create realistic test users:
```bash
python manage.py populate_realistic_users --count 50
```

For more information, see `REALISTIC_USER_GUIDE.md`.

## 🚢 Deployment

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Add environment variables in Railway dashboard
3. Railway will automatically detect and deploy the Django app
4. Configure PostgreSQL database addon
5. Set up Stripe webhook endpoint

For detailed deployment instructions, see `DEPLOYMENT_GUIDE.md`.

### Environment Variables for Production

Ensure these are set in your production environment:

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://...
SENDGRID_API_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_PUBLISHABLE_KEY=...
STRIPE_WEBHOOK_SECRET=...
```

## 🔐 Security Considerations

- **SECRET_KEY**: Never commit your secret key to version control
- **DEBUG**: Always set to `False` in production
- **ALLOWED_HOSTS**: Configure with your production domain
- **CSRF Protection**: Enabled by default in Django
- **HTTPS**: Use HTTPS in production (configured via hosting platform)
- **Database**: Use strong passwords for production databases

## 📚 Additional Documentation

- **Communities Guide**: `COMMUNITIES_GUIDE.md` - Detailed community features
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - Production deployment steps
- **User Population**: `REALISTIC_USER_GUIDE.md` - Creating test users
- **Stripe Setup**: `STRIPE_WEBHOOK_TROUBLESHOOTING.md` - Payment configuration
- **SendGrid Setup**: `SENDGRID_TROUBLESHOOTING.md` - Email configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is part of a capstone project. All rights reserved.

## 👥 Authors

- Capstone Project Team

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap for the UI components
- Stripe for payment processing
- All open-source contributors whose packages made this project possible

## 📞 Support

For issues, questions, or contributions, please open an issue on the repository.

---

**Built with ❤️ using Django**

