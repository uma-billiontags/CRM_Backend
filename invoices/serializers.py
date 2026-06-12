
from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    campaign_id = serializers.CharField(source='campaign.campaign_id', read_only=True)
    client_id = serializers.CharField(source='client.client_id', read_only=True)
    campaign_name = serializers.CharField(source='campaign.campaign_name', read_only=True)
    campaign_end_date = serializers.DateField(source='campaign.end_date', read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_id', 'client_id', 'campaign_id', 'campaign_name', 'campaign_end_date', 'generated_at']
        read_only_fields = ['invoice_id', 'generated_at']