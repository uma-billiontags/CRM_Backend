from django.urls import path
from .  import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/', views.home, name='home'),
    path('create_client/', views.create_client, name='create_client'),
    path('update_client_status/<str:client_id>/', views.update_client_status, name='update_client_status'),
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
    path('download_backup_image/<int:thirdparty_id>/', views.download_backup_image, name='download_backup_image'),
    #path('get_clients_for_approval/', views.get_clients_for_approval, name='get_clients_for_approval'),
    path('approve_client/', views.approve_client, name='approve_client'),
    #path('get_approval_details/<str:client_id>/', views.get_approval_details, name='get_approval_details'),
    path('create_team_member/', views.create_team_member, name='create_team_member'),
    path('get_team_members/', views.get_team_members, name='get_team_members'),
    path('edit_team_member/<int:id>/', views.edit_team_member, name='edit_team_member'),
    path('delete_team_member/<int:id>/', views.delete_team_member, name='delete_team_member'),  
    path('get_client_users/', views.get_client_users, name='get_client_users'),
    path('delete_client_user/<int:id>/', views.delete_client_user, name='delete_client_user'),
    path('edit_client_user/<int:id>/', views.edit_client_user, name='edit_client_user'),
    path('delete_campaign/<str:campaign_id>/', views.delete_campaign, name='delete_campaign'),
    path('approve_campaign/<int:pk>/', views.approve_campaign, name='approve_campaign'),

    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# runserver: daphne CRM_Backend.asgi:application




