
# Claude

# re_path is Django's way of defining a URL pattern using a regular expression instead of the simpler path() syntax. You need regex here because the channel name (campaign_id) is a dynamic segment that has to be extracted from the URL.
from django.urls import re_path             # It handle websocket request (ws://localhost:8000/ws/chat/CAMP001/)
from .consumer import ChatConsumer          

websocket_urlpatterns = [
    re_path(
        r'ws/chat/(?P<campaign_id>[^/]+)/$',  # 'r' means raw string (Regex pattern) - dynamic parameter
        ChatConsumer.as_asgi()
    ),
]