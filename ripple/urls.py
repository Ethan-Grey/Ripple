from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    path('admin-panel/', include('skill_admin.urls')),
    
    # Auth URLs
    path('accounts/', include('allauth.urls')),
    
    # App URLs - Core handles the root path
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('communities/', include('communities.urls')),
    path('chat/', include('chat.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)