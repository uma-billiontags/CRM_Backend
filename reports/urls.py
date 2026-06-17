from django.urls import path
from .  import views

urlpatterns = [
   
    path('generate_campaign_excel/<str:campaign_id>/', views.generate_campaign_excel, name='generate_campaign_excel'),
    path('download_campaign_excel/<str:campaign_id>/', views.download_campaign_excel, name='download_campaign_excel'),
    path('get_campaigns_excel_list/', views.get_campaigns_excel_list, name='get_campaigns_excel_list'),
  
    path('save_excel_edits_to_db/<str:campaign_id>/', views.save_excel_edits_to_db),
    path('publish_campaign_excel/<str:campaign_id>/', views.publish_campaign_excel, name='publish_campaign_excel'),
    path('get_line_item_excel_data/<str:campaign_id>/', views.get_line_item_excel_data, name='get_line_item_excel_data'),
    
    path('add_daily_entry/<str:campaign_id>/', views.add_daily_entry, name='add_daily_entry'),
    path('get_daily_entries/<str:campaign_id>/', views.get_daily_entries, name='get_daily_entries'),
    path('generate_daily_report_excel/<str:campaign_id>/', views.generate_daily_report_excel, name='generate_daily_report_excel'),
    path('download_daily_report_excel/<str:campaign_id>/', views.download_daily_report_excel, name='download_daily_report_excel'),
    path('bulk_upload_daily_entries/', views.bulk_upload_daily_entries, name='bulk_upload_daily_entries'),

] 



# runserver: daphne CRM_Backend.asgi:application



