from channels.generic.websocket import AsyncWebsocketConsumer

import json


class NotificationConsumer(     # handles websocket connect, disconnet and message events.
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.group_name = "notifications"

        await self.channel_layer.group_add(

            self.group_name,

            self.channel_name
        )

        await self.accept()  # Connection accepted successfully

    async def disconnect(
        self,
        close_code
    ):

        await self.channel_layer.group_discard(

            self.group_name,

            self.channel_name
        )

    async def send_notification(
        self,
        event
    ):

        await self.send(text_data=json.dumps({

            "message":
            event["message"]

        }))


