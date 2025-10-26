# accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"  

urlpatterns = [
    path('superadmin/', views.superadminlogin, name='superadminlogin'),
    path('superadmin-dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),

    # Admin URLs
    path('adminlogin/', views.adminlogin, name='adminlogin'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Customer Service URLs
    path('cslogin/', views.customerservicelogin, name='customerservicelogin'),
    path('cs-dashboard/', views.customerservice_dashboard, name='customerservice_dashboard'),
    # Regular user register
    path('register/', views.user_register, name='user_register'),
    # Regular user login
    path('userlogin/', views.user_login, name='user_login'),
    

    path('profile/', views.profile_view, name='profile'),
    path('payment/', views.payment_view, name='payment'),
    path('settings/', views.settings_view, name='settings'),
    path('faq/', views.faq_view, name='faq'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('balance/', views.balance_view, name='balance'),
    path('activities/', views.activities_view, name='activities'),
]
