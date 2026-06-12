from django.urls import path
from .  import views

urlpatterns = [
   # Claude
    path('get_chat_history/<str:campaign_id>/', views.get_chat_history, name='get_chat_history'),
    path('mark_messages_read/<str:campaign_id>/', views.mark_messages_read, name='mark_messages_read'),
    path('get_all_chat_rooms/', views.get_all_chat_rooms, name='get_all_chat_rooms'),
    
    path('send_chat_file/<str:campaign_id>/', views.send_chat_file, name='send_chat_file'),
    
] 



# runserver: daphne CRM_Backend.asgi:application



