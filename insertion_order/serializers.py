from rest_framework import serializers
from .models import *

class InsertionOrderSerializer(serializers.ModelSerializer):
    campaign_id = serializers.CharField(source='campaign.campaign_id', read_only=True)
    client_id = serializers.CharField(source='client.client_id', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = InsertionOrder
        fields = ['id', 'io_id', 'client_id', 'campaign_id', 'pdf_file', 'pdf_url', 'created_at']
        read_only_fields = ['io_id', 'created_at']

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None

