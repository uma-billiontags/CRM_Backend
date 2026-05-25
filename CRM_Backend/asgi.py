"""
ASGI config for CRM_Backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter

# from app.routing import websocket_urlpatterns


# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM_Backend.settings')

# #application = get_asgi_application()

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": URLRouter(

#         websocket_urlpatterns),
# })


import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

from app.routing import websocket_urlpatterns

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'CRM_Backend.settings'
)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({

    "http": django_asgi_app,

    "websocket": AuthMiddlewareStack(

        URLRouter(
            websocket_urlpatterns
        )
    ),
})

# HTTP requests → normal Django
# WebSocket requests → NotificationConsumer


