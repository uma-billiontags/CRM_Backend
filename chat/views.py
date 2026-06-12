from .models import ChatRoom, Message
from .serializers import MessageSerializer
from rest_framework.response import Response 
from rest_framework.decorators import api_view, parser_classes
from accounts.models import User
from campaigns.models import Campaign
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


# Create your views here.
