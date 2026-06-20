# asgi.py is essentially the switchboard — it's the one file that decides "is this an HTTP request or a WebSocket request
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM_Backend.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})