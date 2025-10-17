from django.urls import path
from . import views

app_name = 'skill_admin'

urlpatterns = [
    path('skill-review/', views.skill_review, name='skill_review'),
    path('skill-detail/<int:user_id>/<int:skill_id>/', views.skill_detail, name='skill_detail'),
    path('verify-skill/<int:user_id>/<int:skill_id>/', views.verify_skill, name='verify_skill'),
    path('reject-skill/<int:user_id>/<int:skill_id>/', views.reject_skill, name='reject_skill'),
]
