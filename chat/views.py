from .models import ChatRoom, Message, GeneralChatRoom, GeneralMessage, InternalChatRoom, InternalMessage, CampaignTeamChatRoom, CampaignTeamMessage
from .serializers import MessageSerializer, GeneralMessageSerializer, InternalMessageSerializer, CampaignTeamMessageSerializer
from rest_framework.response import Response 
from rest_framework.decorators import api_view, parser_classes
from accounts.models import User
from campaigns.models import Campaign
from clients.models import Client
from rest_framework.parsers import MultiPartParser, FormParser
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@api_view(['GET'])
def get_chat_history(request, campaign_id):

    try:

        # ==========================
        # FIND CHAT ROOM
        # ==========================

        try:
            room = ChatRoom.objects.get(
                campaign__campaign_id=campaign_id
            )
        except ChatRoom.DoesNotExist:
            return Response([], status=200)

        # ==========================
        # GET MESSAGES
        # ==========================

        messages = Message.objects.filter(
            room=room
        ).select_related(
            'sender'
        ).order_by('timestamp')  # oldest first → WhatsApp style

        serializer = MessageSerializer(
            messages,
            many=True,
            context={'request': request}  # ← ADD THIS LINE
        )

        return Response(serializer.data, status=200)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )


# ==============================
# MARK MESSAGES AS READ
# ==============================

@api_view(['POST'])
def mark_messages_read(request, campaign_id):

    try:

        room = ChatRoom.objects.get(
            campaign__campaign_id=campaign_id
        )

        Message.objects.filter(
            room=room,
            is_read=False,
            sender_type='client'
        ).update(is_read=True)

        return Response(
            {"message": "Marked as read"},
            status=200
        )

    except ChatRoom.DoesNotExist:
        return Response(
            {"error": "Room not found"},
            status=404
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )


# ==============================
# GET ALL CHAT ROOMS (Admin view)
# ==============================

@api_view(['GET'])
def get_all_chat_rooms(request):

    try:

        rooms = ChatRoom.objects.select_related(
            'campaign',
            'client'
        ).all().order_by('-created_at')

        data = []

        for room in rooms:

       
            last_message = Message.objects.filter(
                room=room
            ).order_by('-timestamp').first()

            # Unread count
            unread_count = Message.objects.filter(
                room=room,
                is_read=False,
                sender_type='client'
            ).count()

            data.append({
                "room_id":       room.id,
                "campaign_id":   room.campaign.campaign_id,
                "campaign_name": room.campaign.campaign_name,
                "client_id":     room.client.client_id,
                "client_name":   room.client.name,
                "last_message":  last_message.content if last_message else None,
                "last_time":     last_message.timestamp.isoformat() if last_message else None,
                "unread_count":  unread_count,
            })

        return Response(data, status=200)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def send_chat_file(request, campaign_id):

    try:

        # ── GET FILE ────────────────────────────────
        file        = request.FILES.get('file')
        sender_id   = request.data.get('sender_id')
        sender_type = request.data.get('sender_type')
        content     = request.data.get('content', '')

        if not file or not sender_id:
            return Response({"error": "file and sender_id required"}, status=400)

        # ── FIND ROOM ────────────────────────────────
        try:
            room = ChatRoom.objects.get(campaign__campaign_id=campaign_id)
        except ChatRoom.DoesNotExist:
            campaign = Campaign.objects.get(campaign_id=campaign_id)
            room = ChatRoom.objects.create(
                campaign=campaign,
                client=campaign.client
            )

        # ── DETECT FILE TYPE ─────────────────────────
        file_type = file.content_type  # e.g. image/jpeg, video/mp4

        if file_type.startswith('image/'):
            message_type = 'image'
        elif file_type.startswith('video/'):
            message_type = 'video'
        else:
            message_type = 'file'

        # ── FILE SIZE ─────────────────────────────────
        size = file.size
        if size < 1024 * 1024:
            file_size = f"{size // 1024} KB"
        else:
            file_size = f"{size / (1024 * 1024):.1f} MB"

        # ── SAVE MESSAGE ──────────────────────────────
        sender  = User.objects.get(id=sender_id)
        message = Message.objects.create(
            room=room,
            sender=sender,
            sender_type=sender_type,
            content=content,
            message_type=message_type,
            file=file,
            file_name=file.name,
            file_size=file_size,
        )

        # ── BROADCAST VIA WEBSOCKET ───────────────────
        channel_layer = get_channel_layer()
        room_group    = f"chat_{campaign_id}"

        file_url = request.build_absolute_uri(message.file.url)

        async_to_sync(channel_layer.group_send)(
            room_group,
            {
                'type':         'chat_message',
                'message_id':   message.id,
                'content':      content,
                'sender_id':    sender_id,
                'sender_type':  sender_type,
                'message_type': message_type,
                'file_url':     message.file.url,
                'file_name':    file.name,
                'file_size':    file_size,
                'timestamp':    message.timestamp.isoformat(),
            }
        )

        return Response({
            "message": "File sent successfully",
            "file_url": file_url,
            "message_type": message_type,
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)



# ==============================
# GENERAL CHAT — HISTORY
# ==============================

@api_view(['GET'])
def get_general_chat_history(request, client_id):
    try:
        try:
            room = GeneralChatRoom.objects.get(client__client_id=client_id)
        except GeneralChatRoom.DoesNotExist:
            return Response([], status=200)

        messages = GeneralMessage.objects.filter(room=room).select_related('sender').order_by('timestamp')
        serializer = GeneralMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ==============================
# GENERAL CHAT — MARK READ
# ==============================

@api_view(['POST'])
def mark_general_messages_read(request, client_id):
    try:
        room = GeneralChatRoom.objects.get(client__client_id=client_id)

        # who is marking as read? the requester role tells us whose messages to flip
        reader_type = request.data.get('reader_type', 'admin')  # 'admin' marks client msgs read, 'client' marks admin msgs read
        sender_to_clear = 'client' if reader_type == 'admin' else 'admin'

        GeneralMessage.objects.filter(
            room=room, is_read=False, sender_type=sender_to_clear
        ).update(is_read=True)

        return Response({"message": "Marked as read"}, status=200)

    except GeneralChatRoom.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ==============================
# GENERAL CHAT — ADMIN "Messages" SIDEBAR LIST
# ==============================

@api_view(['GET'])
def get_all_general_chat_rooms(request):
    try:
        rooms = GeneralChatRoom.objects.select_related('client').all().order_by('-created_at')
        data = []

        for room in rooms:
            last_message = GeneralMessage.objects.filter(room=room).order_by('-timestamp').first()

            unread_count = GeneralMessage.objects.filter(
                room=room, is_read=False, sender_type='client'
            ).count()

            data.append({
                "room_id":      room.id,
                "client_id":    room.client.client_id,
                "client_name":  room.client.name,
                "last_message": last_message.content if last_message else None,
                "last_time":    last_message.timestamp.isoformat() if last_message else None,
                "unread_count": unread_count,
            })

        return Response(data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ==============================
# GENERAL CHAT — FILE UPLOAD
# ==============================

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def send_general_chat_file(request, client_id):
    try:
        file        = request.FILES.get('file')
        sender_id   = request.data.get('sender_id')
        sender_type = request.data.get('sender_type')
        content     = request.data.get('content', '')

        if not file or not sender_id:
            return Response({"error": "file and sender_id required"}, status=400)

        try:
            room = GeneralChatRoom.objects.get(client__client_id=client_id)
        except GeneralChatRoom.DoesNotExist:
            client = Client.objects.get(client_id=client_id)
            room = GeneralChatRoom.objects.create(client=client)

        file_type = file.content_type
        if file_type.startswith('image/'):
            message_type = 'image'
        elif file_type.startswith('video/'):
            message_type = 'video'
        else:
            message_type = 'file'

        size = file.size
        if size < 1024 * 1024:
            file_size = f"{size // 1024} KB"
        else:
            file_size = f"{size / (1024 * 1024):.1f} MB"

        sender  = User.objects.get(id=sender_id)
        message = GeneralMessage.objects.create(
            room=room,
            sender=sender,
            sender_type=sender_type,
            content=content,
            message_type=message_type,
            file=file,
            file_name=file.name,
            file_size=file_size,
        )

        channel_layer = get_channel_layer()
        room_group    = f"general_chat_{client_id}"
        file_url      = request.build_absolute_uri(message.file.url)

        async_to_sync(channel_layer.group_send)(
            room_group,
            {
                'type':         'chat_message',
                'message_id':   message.id,
                'content':      content,
                'sender_id':    sender_id,
                'sender_type':  sender_type,
                'message_type': message_type,
                'file_url':     file_url,   # ← sending ABSOLUTE url here (fixes the relative-url issue from campaign chat)
                'file_name':    file.name,
                'file_size':    file_size,
                'timestamp':    message.timestamp.isoformat(),
            }
        )

        return Response({
            "message": "File sent successfully",
            "file_url": file_url,
            "message_type": message_type,
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


from accounts.models import TeamAccess  # add this import alongside the existing User import


@api_view(['GET'])
def get_internal_chat_history(request, user_id):
    try:
        try:
            room = InternalChatRoom.objects.get(member_id=user_id)
        except InternalChatRoom.DoesNotExist:
            return Response([], status=200)

        messages = InternalMessage.objects.filter(room=room).order_by('timestamp')
        serializer = InternalMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def mark_internal_messages_read(request, user_id):
    try:
        room = InternalChatRoom.objects.get(member_id=user_id)
        reader_type = request.data.get('reader_type', 'admin')
        sender_to_clear = 'member' if reader_type == 'admin' else 'admin'

        InternalMessage.objects.filter(
            room=room, is_read=False, sender_type=sender_to_clear
        ).update(is_read=True)

        return Response({"message": "Marked as read"}, status=200)
    except InternalChatRoom.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_all_internal_chat_rooms(request):
    try:
        rooms = InternalChatRoom.objects.all().order_by('-created_at')
        data = []

        for room in rooms:
            member = room.member  # TeamAccess instance via property, may be None if deleted
            if member is None:
                continue  # orphaned room (TeamAccess was deleted) — skip from sidebar

            last_message = InternalMessage.objects.filter(room=room).order_by('-timestamp').first()
            unread_count = InternalMessage.objects.filter(
                room=room, is_read=False, sender_type='member'
            ).count()

            data.append({
                "room_id": room.id,
                "user_id": member.id,
                "member_name": member.member,
                "member_role": member.role,
                "last_message": last_message.content if last_message else None,
                "last_time": last_message.timestamp.isoformat() if last_message else None,
                "unread_count": unread_count,
            })

        return Response(data, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


def _resolve_internal_sender_name(sender_id, sender_type):
    for Model in (TeamAccess, User):
        try:
            obj = Model.objects.get(id=sender_id)
            return obj.member if Model is TeamAccess else obj.username
        except Model.DoesNotExist:
            continue
    return None


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def send_internal_chat_file(request, user_id):
    try:
        file = request.FILES.get('file')
        sender_id = request.data.get('sender_id')
        sender_type = request.data.get('sender_type')
        content = request.data.get('content', '')

        if not file or not sender_id:
            return Response({"error": "file and sender_id required"}, status=400)

        try:
            room = InternalChatRoom.objects.get(member_id=user_id)
        except InternalChatRoom.DoesNotExist:
            TeamAccess.objects.get(id=user_id)  # validates the room owner exists
            room = InternalChatRoom.objects.create(member_id=user_id)

        file_type = file.content_type
        if file_type.startswith('image/'):
            message_type = 'image'
        elif file_type.startswith('video/'):
            message_type = 'video'
        else:
            message_type = 'file'

        size = file.size
        file_size = f"{size // 1024} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"

        sender_name = _resolve_internal_sender_name(sender_id, sender_type)
        if sender_name is None:
            return Response({"error": "Sender not found"}, status=400)

        message = InternalMessage.objects.create(
            room=room, sender_id=sender_id, sender_name=sender_name, sender_type=sender_type,
            content=content, message_type=message_type, file=file,
            file_name=file.name, file_size=file_size,
        )

        channel_layer = get_channel_layer()
        room_group = f"internal_chat_{user_id}"
        file_url = request.build_absolute_uri(message.file.url)

        async_to_sync(channel_layer.group_send)(
            room_group,
            {
                'type': 'chat_message',
                'message_id': message.id,
                'content': content,
                'sender_id': sender_id,
                'sender_type': sender_type,
                'message_type': message_type,
                'file_url': file_url,
                'file_name': file.name,
                'file_size': file_size,
                'timestamp': message.timestamp.isoformat(),
            }
        )

        return Response({"message": "File sent successfully", "file_url": file_url, "message_type": message_type}, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def get_campaign_team_chat_history(request, campaign_id, team_type):
    try:
        try:
            room = CampaignTeamChatRoom.objects.get(
                campaign__campaign_id=campaign_id, team_type=team_type
            )
        except CampaignTeamChatRoom.DoesNotExist:
            return Response([], status=200)

        messages = CampaignTeamMessage.objects.filter(room=room).order_by('timestamp')
        serializer = CampaignTeamMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def mark_campaign_team_messages_read(request, campaign_id, team_type):
    try:
        room = CampaignTeamChatRoom.objects.get(
            campaign__campaign_id=campaign_id, team_type=team_type
        )
        reader_type = request.data.get('reader_type', 'admin')
        sender_to_clear = 'member' if reader_type == 'admin' else 'admin'

        CampaignTeamMessage.objects.filter(
            room=room, is_read=False, sender_type=sender_to_clear
        ).update(is_read=True)

        return Response({"message": "Marked as read"}, status=200)

    except CampaignTeamChatRoom.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Admin sidebar list — all campaigns that have a thread for this team_type
@api_view(['GET'])
def get_all_campaign_team_chat_rooms(request, team_type):
    try:
        rooms = CampaignTeamChatRoom.objects.filter(
            team_type=team_type
        ).select_related('campaign').order_by('-created_at')

        data = []
        for room in rooms:
            last_message = CampaignTeamMessage.objects.filter(room=room).order_by('-timestamp').first()
            unread_count = CampaignTeamMessage.objects.filter(
                room=room, is_read=False, sender_type='member'
            ).count()

            data.append({
                "room_id":       room.id,
                "campaign_id":   room.campaign.campaign_id,
                "campaign_name": room.campaign.campaign_name,
                "last_message":  last_message.content if last_message else None,
                "last_time":     last_message.timestamp.isoformat() if last_message else None,
                "unread_count":  unread_count,
            })

        return Response(data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


def _resolve_campaign_team_sender_name(sender_id, sender_type):
    for Model in (TeamAccess, User):
        try:
            obj = Model.objects.get(id=sender_id)
            return obj.member if Model is TeamAccess else obj.username
        except Model.DoesNotExist:
            continue
    return None


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def send_campaign_team_chat_file(request, campaign_id, team_type):
    try:
        file        = request.FILES.get('file')
        sender_id   = request.data.get('sender_id')
        sender_type = request.data.get('sender_type')
        content     = request.data.get('content', '')

        if not file or not sender_id:
            return Response({"error": "file and sender_id required"}, status=400)

        try:
            room = CampaignTeamChatRoom.objects.get(
                campaign__campaign_id=campaign_id, team_type=team_type
            )
        except CampaignTeamChatRoom.DoesNotExist:
            campaign = Campaign.objects.get(campaign_id=campaign_id)
            room = CampaignTeamChatRoom.objects.create(campaign=campaign, team_type=team_type)

        file_type = file.content_type
        if file_type.startswith('image/'):
            message_type = 'image'
        elif file_type.startswith('video/'):
            message_type = 'video'
        else:
            message_type = 'file'

        size = file.size
        file_size = f"{size // 1024} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"

        sender_name = _resolve_campaign_team_sender_name(sender_id, sender_type)
        if sender_name is None:
            return Response({"error": "Sender not found"}, status=400)

        message = CampaignTeamMessage.objects.create(
            room=room, sender_id=sender_id, sender_name=sender_name, sender_type=sender_type,
            content=content, message_type=message_type, file=file,
            file_name=file.name, file_size=file_size,
        )

        channel_layer = get_channel_layer()
        room_group    = f"campaign_team_chat_{campaign_id}_{team_type}"
        file_url      = request.build_absolute_uri(message.file.url)

        async_to_sync(channel_layer.group_send)(
            room_group,
            {
                'type':         'chat_message',
                'message_id':   message.id,
                'content':      content,
                'sender_id':    sender_id,
                'sender_type':  sender_type,
                'message_type': message_type,
                'file_url':     file_url,
                'file_name':    file.name,
                'file_size':    file_size,
                'timestamp':    message.timestamp.isoformat(),
            }
        )

        return Response({
            "message": "File sent successfully",
            "file_url": file_url,
            "message_type": message_type,
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
