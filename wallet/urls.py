from django.urls import path
from .views import bind_user_wallet_view, withdraw_view
from django.urls import path
from . import views

app_name = "wallet"  # namespaced for safety

urlpatterns = [
    path("bind/", bind_user_wallet_view, name="bind_user_wallet"),
    
    path("withdraw/", withdraw_view, name="withdraw"),

    
    path('withdraw/approve/<int:withdrawal_id>/', views.approve_withdrawal, name='approve_withdrawal'),
    path('withdraw/reject/<int:withdrawal_id>/', views.reject_withdrawal, name='reject_withdrawal'),
]
