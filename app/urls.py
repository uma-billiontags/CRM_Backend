from django.urls import path
from .  import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/', views.home, name='home'),
    path('create_customer/', views.create_customer, name='create_customer'),
    path('get_customers/', views.get_customers, name='get_customers'),
    path('create_client/', views.create_client, name='create_client'),
    path('get_clients/', views.get_clients, name='get_clients'),
    path('login_view/', views.login_view, name='login_view'),
    path('create_campaign/', views.create_campaign, name='create_campaign'),
    path('get_campaigns/', views.get_campaigns, name='get_campaigns'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)