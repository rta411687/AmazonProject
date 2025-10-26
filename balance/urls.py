from django.urls import path
from . import views

app_name = "balance"

urlpatterns = [
    path('approve-voucher/<int:voucher_id>/', views.approve_voucher, name='approve_voucher'),
    path('reject-voucher/<int:voucher_id>/', views.reject_voucher, name='reject_voucher'),

    # Wallet page (GET)
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),

    # Recharge POST (Continue button)
    path('recharge/', views.recharge_amount, name='recharge_amount'),

    # Upload voucher page
    path('upload-voucher/<int:recharge_id>/', views.upload_voucher_view, name='upload_voucher'),
    # update balance 
 
    path('update-recharge-amount/<int:recharge_id>/', views.update_recharge_amount, name='update_recharge_amount'),
]
