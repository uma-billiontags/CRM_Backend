"""
ASGI config for CRM_Backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# Claude
# import os

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from app.routing import websocket_urlpatterns

# os.environ.setdefault(
#     'DJANGO_SETTINGS_MODULE',
#     'CRM_Backend.settings'
# )

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": URLRouter(
#         websocket_urlpatterns
#     ),
# })









import os

from django.core.asgi import get_asgi_application

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'CRM_Backend.settings'
)

application = get_asgi_application()



# HTTP requests → normal Django
# WebSocket requests → NotificationConsumer


