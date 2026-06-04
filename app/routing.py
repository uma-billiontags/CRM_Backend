
# Claude

from django.urls import re_path             # It handle websocket request (ws://localhost:8000/ws/chat/CAMP001/)
from .consumer import ChatConsumer          

websocket_urlpatterns = [
    re_path(
        r'ws/chat/(?P<campaign_id>[^/]+)/$',  # 'r' means raw string (Regex pattern) - dynamic parameter
        ChatConsumer.as_asgi()
    ),
]