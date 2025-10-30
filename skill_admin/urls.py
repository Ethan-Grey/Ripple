from django.urls import path
from . import views

app_name = 'skill_admin'

urlpatterns = [
    # Repurposed routes (keep names for compatibility)
    path('skill-review/', views.skill_review, name='skill_review'),
    path('skill-detail/<int:application_id>/', views.skill_detail, name='skill_detail'),
    path('verify-skill/<int:application_id>/', views.verify_skill, name='verify_skill'),
    path('reject-skill/<int:application_id>/', views.reject_skill, name='reject_skill'),

    # Optional clearer aliases
    path('teacher-review/', views.skill_review, name='teacher_review'),
    path('teacher-detail/<int:application_id>/', views.skill_detail, name='teacher_detail'),
    path('approve-application/<int:application_id>/', views.verify_skill, name='approve_application'),
    path('reject-application/<int:application_id>/', views.reject_skill, name='reject_application'),
]
