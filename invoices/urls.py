from django.urls import path
from .  import views

urlpatterns = [
    path('generate_invoice_pdf/<str:campaign_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    path('download_invoice_pdf/<str:campaign_id>/', views.download_invoice_pdf, name='download_invoice_pdf'),    
    
    path('get_invoice_list_by_client/<str:client_id>/', views.get_invoice_list_by_client),

] 



# runserver: daphne CRM_Backend.asgi:application



