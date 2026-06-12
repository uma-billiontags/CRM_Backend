from django.db import models
from clients.models import Client
from campaigns.models import Campaign
from accounts.models import User

# Create your models here.

# # ==============================
# # CHAT ROOM MODEL
# # ==============================

class ChatRoom(models.Model):

    campaign = models.OneToOneField(
        Campaign,
        on_delete=models.CASCADE,
        related_name='chat_room'
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room → {self.campaign.campaign_id} ({self.client.name})"


# # ==============================
# # MESSAGE MODEL
# # ==============================

class Message(models.Model):

    SENDER_TYPE = [
        ('client', 'Client'),
        ('admin',  'Admin'),
    ]
    
    MESSAGE_TYPE = [
        ('text',  'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file',  'File'),
    ]

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPE
    )

    content = models.TextField(blank=True)  # ← make blank=True (file messages may have no text)
    
    # ── NEW FIELDS ──────────────────────────
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE,
        default='text'
    )

    file = models.FileField(
        upload_to='chat/files/',
        null=True,
        blank=True
    )
     
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=50, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']  # oldest first → WhatsApp style

    def __str__(self):
        return f"{self.sender_type} → {self.room} → {self.timestamp:%Y-%m-%d %H:%M}"
    
    