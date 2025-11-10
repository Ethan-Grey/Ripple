from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('dashboard/', views.home, name='home'),
    path('swipe/', views.swipe, name='swipe'),
    path('search/', views.search, name='search'),
    path('skill/<int:skill_id>/', views.skill_detail, name='skill_detail'),
    path('', views.landing, name='landing'),
    path('about/', views.about, name='about'),       
]
