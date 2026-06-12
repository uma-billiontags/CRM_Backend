from django.urls import path
from .  import views

urlpatterns = [
    path('login_view/', views.login_view, name='login_view'),
    path('create_team_member/', views.create_team_member, name='create_team_member'),
    path('get_team_members/', views.get_team_members, name='get_team_members'),
    path('edit_team_member/<int:id>/', views.edit_team_member, name='edit_team_member'),
    path('delete_team_member/<int:id>/', views.delete_team_member, name='delete_team_member'),  
    path('get_client_users/', views.get_client_users, name='get_client_users'),
    path('delete_client_user/<int:id>/', views.delete_client_user, name='delete_client_user'),
    path('edit_client_user/<int:id>/', views.edit_client_user, name='edit_client_user'),
] 


