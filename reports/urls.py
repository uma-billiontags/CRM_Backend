from django.urls import path
from .  import views

urlpatterns = [
   
    path('generate_campaign_excel/<str:campaign_id>/', views.generate_campaign_excel, name='generate_campaign_excel'),
    path('download_campaign_excel/<str:campaign_id>/', views.download_campaign_excel, name='download_campaign_excel'),
    path('get_campaigns_excel_list/', views.get_campaigns_excel_list, name='get_campaigns_excel_list'),
  
    path('save_excel_edits_to_db/<str:campaign_id>/', views.save_excel_edits_to_db),
    path('publish_campaign_excel/<str:campaign_id>/', views.publish_campaign_excel, name='publish_campaign_excel'),
    path('get_line_item_excel_data/<str:campaign_id>/', views.get_line_item_excel_data, name='get_line_item_excel_data'),

] 



# runserver: daphne CRM_Backend.asgi:application



