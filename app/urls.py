from django.urls import path
from .  import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/', views.home, name='home'),
    path('create_client/', views.create_client, name='create_client'),
    path('get_all_clients/', views.get_all_clients, name='get_all_clients'),
    path('get_client/<str:client_id>/', views.get_client, name='get_client'),
    path('create_campaign/', views.create_campaign, name='create_campaign'),
    path('get_campaigns/', views.get_campaigns, name='get_campaigns'),
    path('get_campaigns_by_client/<str:client_id>/', views.get_campaigns_by_client, name='get_campaigns_by_client'),
    path('get_campaign_by_id/<str:campaign_id>/', views.get_campaign_by_id, name='get_campaign_by_id'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)








