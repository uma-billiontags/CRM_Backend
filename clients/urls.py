from django.urls import path
from .  import views

urlpatterns = [
    path('create_client/', views.create_client, name='create_client'),
    path('update_client_status/<str:client_id>/', views.update_client_status, name='update_client_status'),
    path('get_all_clients/', views.get_all_clients, name='get_all_clients'),
    path('get_client/<str:client_id>/', views.get_client, name='get_client'),
    path('approve_client/', views.approve_client, name='approve_client'),
    path('get_client_users/', views.get_client_users, name='get_client_users'),
    path('delete_client_user/<int:id>/', views.delete_client_user, name='delete_client_user'),
    path('edit_client_user/<int:id>/', views.edit_client_user, name='edit_client_user'),

] 



# runserver: daphne CRM_Backend.asgi:application



