from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    # Community browsing
    path('', views.communities_page, name='communities'),
    path('<int:pk>/', views.community_detail, name='community_detail'),
    
    # Join/Leave
    path('<int:pk>/join/', views.join_community, name='join_community'),
    path('<int:pk>/leave/', views.leave_community, name='leave_community'),
    
    # Posts
    path('<int:community_pk>/create-post/', views.create_post, name='create_post'),
    path('<int:community_pk>/post/<int:post_pk>/', views.post_detail, name='post_detail'),
    path('<int:community_pk>/post/<int:post_pk>/delete/', views.delete_post, name='delete_post'),
    
    # Comments
    path('<int:community_pk>/post/<int:post_pk>/comment/', views.add_comment, name='add_comment'),
    
    # Voting
    path('<int:community_pk>/post/<int:post_pk>/vote/', views.vote_post, name='vote_post'),
    path('comment/<int:comment_pk>/vote/', views.vote_comment, name='vote_comment'),
    
    # Community requests
    path('request/', views.request_community, name='request_community'),
    path('my-requests/', views.my_community_requests, name='my_requests'),
    
    # Admin: Community request review
    path('admin/requests/', views.admin_community_requests, name='admin_community_requests'),
    path('admin/requests/<int:request_id>/<str:action>/', views.admin_community_request_action, name='admin_community_request_action'),
    
    # Admin: Delete community
    path('<int:pk>/delete/', views.delete_community, name='delete_community'),
]
