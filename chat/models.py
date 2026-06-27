from django.db import models
from clients.models import Client
from campaigns.models import Campaign
from accounts.models import User

# Create your models here.


# CHAT ROOM MODEL
class ChatRoom(models.Model):

    # One-to-One relationship (One Campaign can have only one ChatRoom. One ChatRoom belongs to only one Campaign.)
    campaign = models.OneToOneField(
        Campaign, on_delete=models.CASCADE, related_name="chat_room"
    )

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="chat_rooms"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room → {self.campaign.campaign_id} ({self.client.name})"


# # ==============================
# # MESSAGE MODEL
# # ==============================


class Message(models.Model):

    SENDER_TYPE = [
        ("client", "Client"),
        ("admin", "Admin"),
    ]

    MESSAGE_TYPE = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"), 
    ]

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")

    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE)

    content = models.TextField(
        blank=True
    )  # ← make blank=True (file messages may have no text)

    # ── NEW FIELDS ──────────────────────────
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default="text")

    file = models.FileField(upload_to="chat/files/", null=True, blank=True)

    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=50, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)
    
    tagged_line_item = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["timestamp"]  # oldest first → WhatsApp style

    def __str__(self):
        return f"{self.sender_type} → {self.room} → {self.timestamp:%Y-%m-%d %H:%M}"


# ==============================
# GENERAL CHAT (Client ↔ Admin, not tied to any campaign)
# ==============================

class GeneralChatRoom(models.Model):

    # One client → exactly one general chat room with admin
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="general_chat_room"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"General Room → {self.client.name}"


class GeneralMessage(models.Model):

    SENDER_TYPE = [
        ("client", "Client"),
        ("admin", "Admin"),
    ]

    MESSAGE_TYPE = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
    ]

    room = models.ForeignKey(
        GeneralChatRoom, on_delete=models.CASCADE, related_name="messages"
    )

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="general_messages"
    )

    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE)

    content = models.TextField(blank=True)

    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default="text")

    file = models.FileField(upload_to="general_chat/files/", null=True, blank=True)

    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=50, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender_type} → {self.room} → {self.timestamp:%Y-%m-%d %H:%M}"
    
class InternalChatRoom(models.Model):

    # member_id stores TeamAccess.id directly — no FK, since TeamAccess
    # and User are separate identity tables and we don't want duplicates
    member_id = models.IntegerField(unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def member(self):
        from accounts.models import TeamAccess
        return TeamAccess.objects.filter(id=self.member_id).first()

    def __str__(self):
        m = self.member
        return f"Internal Room → {m.member if m else self.member_id}"


class InternalMessage(models.Model):

    SENDER_TYPE = [
        ("member", "Team Member"),
        ("admin", "Admin"),
    ]

    MESSAGE_TYPE = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
    ]

    room = models.ForeignKey(
        InternalChatRoom, on_delete=models.CASCADE, related_name="messages"
    )

    # sender_id is TeamAccess.id when sender_type='member',
    # or accounts.User.id when sender_type='admin' — sender_type tells us which
    sender_id = models.IntegerField()
    sender_name = models.CharField(max_length=150, blank=True)  # denormalized, set at creation

    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE)
    content = models.TextField(blank=True)

    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default="text")
    file = models.FileField(upload_to="internal_chat/files/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=50, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender_type} → {self.room} → {self.timestamp:%Y-%m-%d %H:%M}"
    
    
# ==============================
# CAMPAIGN TEAM CHAT (Team ↔ Admin, scoped to a specific campaign)
# ==============================

class CampaignTeamChatRoom(models.Model):

    TEAM_TYPE = [
        ("creative", "Creative Team"),
        ("campaign_team", "Campaign Team"),
    ]

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="team_chat_rooms"
    )

    team_type = models.CharField(max_length=20, choices=TEAM_TYPE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("campaign", "team_type")  # one room per (campaign, team) pair

    def __str__(self):
        return f"{self.get_team_type_display()} Room → {self.campaign.campaign_id}"


class CampaignTeamMessage(models.Model):

    SENDER_TYPE = [
        ("member", "Team Member"),
        ("admin", "Admin"),
    ]

    MESSAGE_TYPE = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
    ]

    room = models.ForeignKey(
        CampaignTeamChatRoom, on_delete=models.CASCADE, related_name="messages"
    )

    # sender_id is TeamAccess.id when sender_type='member', accounts.User.id when 'admin'
    sender_id = models.IntegerField()
    sender_name = models.CharField(max_length=150, blank=True)  # denormalized, set at creation

    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE)
    content = models.TextField(blank=True)

    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default="text")
    file = models.FileField(upload_to="campaign_team_chat/files/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=50, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender_type} → {self.room} → {self.timestamp:%Y-%m-%d %H:%M}"