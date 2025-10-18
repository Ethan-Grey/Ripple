from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True, next_page='/dashboard/', success_url='/dashboard/'), name='login'),
    path('logout/', views.logout_direct, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    
    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset.html',
             email_template_name='password_reset_email.html',
             subject_template_name='password_reset_subject.txt',
             success_url=reverse_lazy('users:password_reset_done')
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/delete-skill/<int:skill_id>/', views.delete_skill, name='delete_skill'),
    path('profile/verify-identity/', views.verify_identity, name='verify_identity'),
    
    # Skill verification URLs
    path('profile/verify-skill/<int:skill_id>/', views.verify_skill, name='verify_skill'),
    path('profile/submit-evidence/<int:skill_id>/', views.submit_evidence, name='submit_evidence'),
    path('profile/remove-evidence/<int:evidence_id>/', views.remove_evidence, name='remove_evidence'),
    path('profile/unverify-skill/<int:skill_id>/', views.unverify_skill, name='unverify_skill'),
    path('profile/add-skill/', views.add_skill, name='add_skill'),
    
    # Admin: User identity verification review
    path('admin/verification/', views.admin_user_verifications, name='admin_user_verifications'),
    path('admin/verification/<int:profile_id>/<str:action>/', views.admin_user_verification_action, name='admin_user_verification_action'),
    
]