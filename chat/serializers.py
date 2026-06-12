from rest_framework import serializers
from .models import *

class MessageSerializer(serializers.ModelSerializer):

    sender_name = serializers.CharField(
        source='sender.username',
        read_only=True
    )
    
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'content',
            'sender_id',
            'sender_name',
            'sender_type',
            'message_type',   # ← new
            'file',           # ← new
            'file_url',       # ← new
            'file_name',      # ← new
            'file_size',      # ← new
            'timestamp',
            'is_read',
        ]
        
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
