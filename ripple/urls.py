from django.contrib import admin
from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    path('admin-panel/', include('skill_admin.urls')),
    
    # Auth URLs
    path('accounts/', include('allauth.urls')),
    
    # User authentication URLs - must come BEFORE landing page
    path('login/', include('users.urls')),
    path('register/', include('users.urls')),
    path('profile/', include('users.urls')),
    path('password-reset/', include('users.urls')),
    
    # Main app URLs (specific paths)
    path('dashboard/', views.home, name='home'),
    path('swipe/', views.swipe, name='swipe'),
    path('communities/', views.communities_page, name='communities'),
    path('messages/', views.messages_page, name='messages'),
    path('search/', views.search, name='search'),
    
    # Landing page (at root) - must be LAST
    path('', views.landing, name='landing'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)