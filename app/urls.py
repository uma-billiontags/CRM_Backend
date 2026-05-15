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
    path('update_campaign/<str:campaign_id>/',views.update_campaign, name='update_campaign'),
    path('login_view/', views.login_view, name='login_view'),
    path('download_creative/<int:creative_id>/', views.download_creative, name='download_creative'),
    path('download_thirdparty/<int:thirdparty_id>/', views.download_thirdparty, name='download_thirdparty'),
    path('download_backup_image/<int:thirdparty_id>/', views.download_backup_image, name='download_backup_image')

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)









