from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import CampaignTeamChatRoom, CampaignTeamMessage
from campaigns.models import Campaign
from accounts.models import User, TeamAccess
from .notification import send_push_notification
import json


class CampaignTeamChatConsumer(AsyncWebsocketConsumer):
    # ws/campaign-team-chat/CAMP001/creative/   or   .../campaign_team/

    async def connect(self):
        self.campaign_id = self.scope['url_route']['kwargs']['campaign_id']
        self.team_type = self.scope['url_route']['kwargs']['team_type']

        valid_types = dict(CampaignTeamChatRoom.TEAM_TYPE)
        if self.team_type not in valid_types:
            await self.close()
            return

        self.room_group_name = f"campaign_team_chat_{self.campaign_id}_{self.team_type}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"Campaign Team Chat Connected → {self.campaign_id} ({self.team_type})")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"Campaign Team Chat Disconnected → {self.campaign_id} ({self.team_type})")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            content = data.get('content', '').strip()
            sender_id = data.get('sender_id')
            sender_type = data.get('sender_type')  # 'member' or 'admin'

            if not content or not sender_id:
                return

            room = await self.get_or_create_room(self.campaign_id, self.team_type)
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
            print(f"Campaign Team Chat Receive Error: {e}")

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
    def get_or_create_room(self, campaign_id, team_type):
        try:
            campaign = Campaign.objects.get(campaign_id=campaign_id)
        except Campaign.DoesNotExist:
            print(f"Campaign not found: {campaign_id}")
            return None

        room, _ = CampaignTeamChatRoom.objects.get_or_create(
            campaign=campaign, team_type=team_type
        )
        return room

    @staticmethod
    def _resolve_sender_name(sender_id, sender_type):
        # checks TeamAccess first, falls back to accounts.User — same pattern as InternalChatConsumer
        for Model in (TeamAccess, User):
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

        return CampaignTeamMessage.objects.create(
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
                send_push_notification(
                    title=f"New {self.team_type.replace('_', ' ')} message — {self.campaign_id}",
                    body=content[:100]
                )
        except Exception as e:
            print(f"Campaign Team Chat Notify Error: {e}")