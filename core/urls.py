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
    path('about/', views.about, name='about'),     
    path('contact/', views.contact, name='contact'),  
      
     # Report system
    path('report/', views.report_content, name='report_content'),
    path('report/<str:content_type>/<int:object_id>/', views.quick_report, name='quick_report'),
    path('my-reports/', views.user_reports, name='user_reports'),
    
    # Admin report management
    path('admin-reports/', views.admin_reports, name='admin_reports'),
    path('admin-handle-report/<int:report_id>/', views.admin_handle_report, name='admin_handle_report'),
    
    # Custom admin page
    path('custom-admin/', views.custom_admin, name='custom_admin'),
]
