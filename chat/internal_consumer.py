from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import InternalChatRoom, InternalMessage
from accounts.models import User, TeamAccess
from .notification import send_push_notification
import json


class InternalChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.member_id = self.scope['url_route']['kwargs']['user_id']  # TeamAccess.id of the room owner
        self.room_group_name = f"internal_chat_{self.member_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"Internal Chat Connected → {self.member_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"Internal Chat Disconnected → {self.member_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            content = data.get('content', '').strip()
            sender_id = data.get('sender_id')
            sender_type = data.get('sender_type')  # 'member' or 'admin'

            if not content or not sender_id:
                return

            room = await self.get_or_create_room(self.member_id)
            if room is None:
                return

            message = await self.save_message(room, sender_id, sender_type, content)
            if message is None:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'content': content,
                    'sender_id': sender_id,
                    'sender_type': sender_type,
                    'timestamp': message.timestamp.isoformat(),
                }
            )

            await self.notify(sender_type, content)

        except Exception as e:
            print(f"Internal Chat Receive Error: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'id': event['message_id'],
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_type': event['sender_type'],
            'message_type': event.get('message_type', 'text'),
            'file_url': event.get('file_url', None),
            'file_name': event.get('file_name', None),
            'file_size': event.get('file_size', None),
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def get_or_create_room(self, member_id):
        try:
            TeamAccess.objects.get(id=member_id)
        except TeamAccess.DoesNotExist:
            print(f"TeamAccess member not found: {member_id}")
            return None

        room, _ = InternalChatRoom.objects.get_or_create(member_id=member_id)
        return room

    # ── FIX: resolve sender across BOTH tables, regardless of sender_type ──
    @staticmethod
    def _resolve_sender_name(sender_id, sender_type):
        """
        Returns the display name for a sender, checking TeamAccess first
        (since admin/superadmin/creative/campaign_team can all live there),
        falling back to accounts.User. Returns None if not found anywhere.
        """
        # Prefer the table implied by sender_type first, then fall back.
        if sender_type == 'member':
            order = [TeamAccess, User]
        else:  # 'admin'
            order = [TeamAccess, User]  # admin/superadmin also live in TeamAccess

        for Model in order:
            try:
                obj = Model.objects.get(id=sender_id)
                return obj.member if Model is TeamAccess else obj.username
            except Model.DoesNotExist:
                continue
        return None

    @database_sync_to_async
    def save_message(self, room, sender_id, sender_type, content):
        sender_name = self._resolve_sender_name(sender_id, sender_type)
        if sender_name is None:
            print(f"Sender not found: id={sender_id}, type={sender_type}")
            return None

        return InternalMessage.objects.create(
            room=room,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_type=sender_type,
            content=content,
        )

    @database_sync_to_async
    def notify(self, sender_type, content):
        try:
            if sender_type == 'member':
                send_push_notification(title="New team message", body=content[:100])
        except Exception as e:
            print(f"Internal Chat Notify Error: {e}")