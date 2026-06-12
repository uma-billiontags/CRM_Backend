from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clients.urls')),
    path('', include('accounts.urls')),
    path('', include('campaigns.urls')),
    path('', include('chat.urls')),
    path('', include('notifications.urls')),
    path('', include('reports.urls')),
    path('', include('insertion_order.urls')),
    path('', include('invoices.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
