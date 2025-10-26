from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Accounts app URLs
    path('products/', include('products.urls')), # Products app URLs
    path('balance/', include('balance.urls', namespace='balance')),  # ✅ Namespace added
    path('stoppoints/', include('stoppoints.urls')),
    path('wallet/', include('wallet.urls', namespace='wallet')),
    path("commission/", include("commission.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
