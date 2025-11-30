from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    path('admin-panel/', include('skill_admin.urls')),
    
    # Override allauth inactive account URL
    path('accounts/inactive/', __import__('users.views', fromlist=['']).account_suspended, name='account_inactive'),
    
    # Auth URLs
    path('accounts/', include('allauth.urls')),
    
    # App URLs - Core handles the root path
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('communities/', include('communities.urls')),
    path('chat/', include('chat.urls')),
    path('classes/', include('skills.urls')),
    path('payments/webhooks/stripe/', __import__('skills.views', fromlist=['']).StripeWebhookView.as_view(), name='stripe_webhook'),
    
]

# Serve media files in both development and production
if settings.DEBUG:
    # Development: use static() helper
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Production: serve media files through Django
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]