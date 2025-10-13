"""
URL configuration for ripple project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # auth
    path('accounts/', include('allauth.urls')),
    
    # User authentication URLs
    path('', include('users.urls')),
    
    # Admin URLs
    path('admin-panel/', include('skill_admin.urls')),
    
    # Main app URLs
    path('', views.home, name='home'),
    path('swipe/', views.swipe, name='swipe'),
    path('communities/', views.communities_page, name='communities'),
    path('messages/', views.messages_page, name='messages'),
    path('search/', views.search, name='search'),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
