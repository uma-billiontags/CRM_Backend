from django.urls import path
from . import views

urlpatterns = [
    path('generate_invoice_pdf/<str:campaign_id>/', views.generate_invoice_pdf),
    # ── CHANGED: now uses invoice_id not campaign_id
    path('download_invoice_pdf/<str:invoice_id>/', views.download_invoice_pdf),
    path('get_invoice_list_by_client/<str:client_id>/', views.get_invoice_list_by_client),
    # ── NEW: for client dropdown
    path('get_all_clients/', views.get_all_clients),
]