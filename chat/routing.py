
# Claude

# re_path is Django's way of defining a URL pattern using a regular expression instead of the simpler path() syntax. You need regex here because the channel name (campaign_id) is a dynamic segment that has to be extracted from the URL.
from django.urls import re_path             # It handle websocket request (ws://localhost:8000/ws/chat/CAMP001/)
from .consumer import ChatConsumer          
from .general_consumer import GeneralChatConsumer
from .internal_consumer import InternalChatConsumer
from .campaign_team_consumer import CampaignTeamChatConsumer  # add to imports

websocket_urlpatterns = [
    re_path(
        r'ws/chat/(?P<campaign_id>[^/]+)/$',  # 'r' means raw string (Regex pattern) - dynamic parameter
        ChatConsumer.as_asgi()
    ),
    
    # NEW — general client↔admin chat
    re_path(
        r'ws/general-chat/(?P<client_id>[^/]+)/$',
        GeneralChatConsumer.as_asgi()
    ),
    
    re_path(
        r'ws/internal-chat/(?P<user_id>[^/]+)/$',
        InternalChatConsumer.as_asgi()
    ),
    
    re_path(
        r'ws/campaign-team-chat/(?P<campaign_id>[^/]+)/(?P<team_type>[^/]+)/$',
        CampaignTeamChatConsumer.as_asgi()
    ),
]