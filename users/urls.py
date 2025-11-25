from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    #Application URLs
    path('applications/', views.applications_view, name='applications'),

    # Authentication URLs
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_direct, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    
    # Password reset URLs
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(),
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/verify-identity/', views.verify_identity, name='verify_identity'),
    path('profile/verification-status/', views.view_verification_status, name='verification_status'),
    path('profile/add-skill/', views.add_skill, name='add_skill'),
    path('profile/delete-skill/<int:skill_id>/', views.delete_skill, name='delete_skill'),
    path('profile/verify-skill/<int:skill_id>/', views.verify_skill, name='verify_skill'),
    path('profile/submit-evidence/<int:skill_id>/', views.submit_evidence, name='submit_evidence'),
    path('profile/remove-evidence/<int:evidence_id>/', views.remove_evidence, name='remove_evidence'),
    path('profile/unverify-skill/<int:skill_id>/', views.unverify_skill, name='unverify_skill'),
    path('profile/<str:username>/', views.view_user_profile, name='view_profile'),
    
    # Admin: User identity verification review
    path('user-verification/', views.admin_user_verifications, name='admin_user_verifications'),
    path('user-verification/<int:profile_id>/<str:action>/', views.admin_user_verification_action, name='admin_user_verification_action'),
    
    # Admin: User skills management
    path('admin-user-skills/', views.admin_user_skills, name='admin_user_skills'),
    path('admin-delete-skill/<int:user_id>/<int:skill_id>/', views.admin_delete_user_skill, name='admin_delete_user_skill'),
    
    # Admin: User classes management
    path('admin-user-classes/', views.admin_user_classes, name='admin_user_classes'),
    path('admin-delete-class/<int:class_id>/', views.admin_delete_class, name='admin_delete_class'),
    
]