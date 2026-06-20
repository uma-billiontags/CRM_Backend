from django.urls import path
from . import views

urlpatterns = [
    # EXISTING — campaign chat (untouched)
    path('get_chat_history/<str:campaign_id>/', views.get_chat_history, name='get_chat_history'),
    path('mark_messages_read/<str:campaign_id>/', views.mark_messages_read, name='mark_messages_read'),
    path('get_all_chat_rooms/', views.get_all_chat_rooms, name='get_all_chat_rooms'),
    path('send_chat_file/<str:campaign_id>/', views.send_chat_file, name='send_chat_file'),

    # NEW — general client↔admin chat
    path('get_general_chat_history/<str:client_id>/', views.get_general_chat_history, name='get_general_chat_history'),
    path('mark_general_messages_read/<str:client_id>/', views.mark_general_messages_read, name='mark_general_messages_read'),
    path('get_all_general_chat_rooms/', views.get_all_general_chat_rooms, name='get_all_general_chat_rooms'),
    path('send_general_chat_file/<str:client_id>/', views.send_general_chat_file, name='send_general_chat_file'),
    
    path('get_internal_chat_history/<str:user_id>/', views.get_internal_chat_history, name='get_internal_chat_history'),
    path('mark_internal_messages_read/<str:user_id>/', views.mark_internal_messages_read, name='mark_internal_messages_read'),
    path('get_all_internal_chat_rooms/', views.get_all_internal_chat_rooms, name='get_all_internal_chat_rooms'),
    path('send_internal_chat_file/<str:user_id>/', views.send_internal_chat_file, name='send_internal_chat_file'),
    
    path('get_campaign_team_chat_history/<str:campaign_id>/<str:team_type>/', views.get_campaign_team_chat_history, name='get_campaign_team_chat_history'),
    path('mark_campaign_team_messages_read/<str:campaign_id>/<str:team_type>/', views.mark_campaign_team_messages_read, name='mark_campaign_team_messages_read'),
    path('get_all_campaign_team_chat_rooms/<str:team_type>/', views.get_all_campaign_team_chat_rooms, name='get_all_campaign_team_chat_rooms'),
    path('send_campaign_team_chat_file/<str:campaign_id>/<str:team_type>/', views.send_campaign_team_chat_file, name='send_campaign_team_chat_file'),
]

# runserver: daphne CRM_Backend.asgi:application



