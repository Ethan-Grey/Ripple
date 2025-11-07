from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('dashboard/', views.home, name='home'),
    path('swipe/', views.swipe, name='swipe'),
    path('swipe/action/', views.swipe_action, name='swipe_action'),
    path('swipe/whitelist/', views.view_whitelist, name='whitelist'),
    path('swipe/blacklist/', views.view_blacklist, name='blacklist'),
    path('swipe/remove/<int:class_id>/', views.remove_swipe_action, name='remove_swipe'),
    path('search/', views.search, name='search'),
    path('skill/<int:skill_id>/', views.skill_detail, name='skill_detail'),
    path('', views.landing, name='landing'),
]
