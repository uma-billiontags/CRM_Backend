from django.urls import path
from .  import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('create_campaign/', views.create_campaign, name='create_campaign'),
    path('get_campaigns/', views.get_campaigns, name='get_campaigns'),
    path('get_campaigns_by_client/<str:client_id>/', views.get_campaigns_by_client, name='get_campaigns_by_client'),
    path('get_campaign_by_id/<str:campaign_id>/', views.get_campaign_by_id, name='get_campaign_by_id'),
    path('update_campaign/<str:campaign_id>/',views.update_campaign, name='update_campaign'),
    path('download_creative/<int:creative_id>/', views.download_creative, name='download_creative'),
    path('download_thirdparty/<int:thirdparty_id>/', views.download_thirdparty, name='download_thirdparty'),
    path('download_backup_image/<int:thirdparty_id>/', views.download_backup_image, name='download_backup_image'),
    path('approve_campaign/<int:pk>/', views.approve_campaign, name='approve_campaign'),
    # Creative
    path('update_creative_id/', views.update_creative_id, name='update_creative_id'),
    
    path('update_line_item_dv_id/<str:line_item_id>/', views.update_line_item_dv_id, name='update_line_item_dv_id'),
    
    path('create_bulk_campaign/', views.create_bulk_campaign, name='create_bulk_campaign'),
    
    path('get_bulk_campaigns/', views.get_bulk_campaigns, name='get_bulk_campaigns'),
    path('update_bulk_campaign_status/<int:pk>/', views.update_bulk_campaign_status, name='update_bulk_campaign_status'),
    
] 


# runserver: daphne CRM_Backend.asgi:application



