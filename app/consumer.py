# channels.generic.websocket → Django Channels module for WebSocket handling.
# AsyncWebsocketConsumer → a built-in class that helps create asynchronous WebSocket consumers.

from channels.generic.websocket import AsyncWebsocketConsumer 
import json

# It handle websocket connection, disconnection and message sending to frontend when notification is triggered from backend.

class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.group_name = "notifications"

        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept websocket connection
        await self.accept()

        print("WebSocket Connected")


    async def disconnect(self, close_code):

        # Leave notification group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        print("WebSocket Disconnected")


    # Receive message from group
    async def send_notification(self, event):

        message = event["message"]

        # Send message to frontend
        await self.send(text_data=json.dumps({
            "message": message
        }))

        