from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('communities/', views.communities_page, name='communities'),
]
