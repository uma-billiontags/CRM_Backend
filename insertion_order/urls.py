from django.urls import path
from .  import views

urlpatterns = [
    path('generate_io_pdf/<str:campaign_id>/', views.generate_io_pdf, name='generate_io_pdf'),
    path('download_io_pdf/<str:campaign_id>/', views.download_io_pdf, name='download_io_pdf'),
    
    path('get_io_list_by_client/<str:client_id>/', views.get_io_list_by_client),

] 



# runserver: daphne CRM_Backend.asgi:application



