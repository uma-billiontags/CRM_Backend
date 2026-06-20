from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GeneralChatRoom, GeneralMessage
from clients.models import Client
from accounts.models import User
from .notification import send_push_notification, send_notification_to_client
import json


class GeneralChatConsumer(AsyncWebsocketConsumer):

    # ==============================
    # CONNECT
    # ==============================

    async def connect(self):

        self.client_id = self.scope['url_route']['kwargs']['client_id']
        self.room_group_name = f"general_chat_{self.client_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"General Chat Connected → {self.client_id}")

    # ==============================
    # DISCONNECT
    # ==============================

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"General Chat Disconnected → {self.client_id}")

    # ==============================
    # RECEIVE
    # ==============================

    async def receive(self, text_data):

        try:
            data        = json.loads(text_data)
            content     = data.get('content', '').strip()
            sender_id   = data.get('sender_id')
            sender_type = data.get('sender_type')

            if not content or not sender_id:
                return

            room = await self.get_or_create_room(self.client_id)
            if room is None:
                return

            message = await self.save_message(
                room=room,
                sender_id=sender_id,
                sender_type=sender_type,
                content=content
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type':        'chat_message',
                    'message_id':  message.id,
                    'content':     content,
                    'sender_id':   sender_id,
                    'sender_type': sender_type,
                    'timestamp':   message.timestamp.isoformat(),
                }
            )

            # Notify the OTHER side
            await self.notify(sender_type, content)

        except Exception as e:
            print(f"General Chat Receive Error: {e}")

    # ==============================
    # BROADCAST HANDLER
    # ==============================

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'id':           event['message_id'],
            'message_id':   event['message_id'],
            'content':      event['content'],
            'sender_id':    event['sender_id'],
            'sender_type':  event['sender_type'],
            'message_type': event.get('message_type', 'text'),
            'file_url':     event.get('file_url', None),
            'file_name':    event.get('file_name', None),
            'file_size':    event.get('file_size', None),
            'timestamp':    event['timestamp'],
        }))

    # ==============================
    # DB HELPERS
    # ==============================

    @database_sync_to_async
    def get_or_create_room(self, client_id):
        try:
            client = Client.objects.get(client_id=client_id)
            room, _ = GeneralChatRoom.objects.get_or_create(client=client)
            return room
        except Client.DoesNotExist:
            print(f"Client not found: {client_id}")
            return None

    @database_sync_to_async
    def save_message(self, room, sender_id, sender_type, content):
        sender = User.objects.get(id=sender_id)
        return GeneralMessage.objects.create(
            room=room,
            sender=sender,
            sender_type=sender_type,
            content=content
        )

    # ==============================
    # NOTIFICATIONS (direction-aware)
    # ==============================

    @database_sync_to_async
    def notify(self, sender_type, content):
        try:
            if sender_type == 'client':
                # Notify admin(s)
                send_push_notification(
                    title="New message",
                    body=content[:100]
                )
            else:
                # Notify the client
                client = Client.objects.get(client_id=self.client_id)
                send_notification_to_client(
                    client=client,
                    title="New message from Admin",
                    body=content[:100]
                )
        except Exception as e:
            print(f"General Chat Notify Error: {e}")