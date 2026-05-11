
from rest_framework import serializers
from .models import *
import json


# ==============================  
# CHILD SERIALIZERS
# ==============================

class ClientBillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientBilling
        exclude = ['client']


class ClientOwnershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientOwnership
        exclude = ['client']


class ClientClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientClassification
        exclude = ['client']


#  NEW: Address Serializer (MULTIPLE)
class CompanyAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAddress
        exclude = ['client']


#  NEW: Contact Serializer (MULTIPLE)
class CompanyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyContact
        exclude = ['client']



class ClientSerializer(serializers.ModelSerializer):

    billing = ClientBillingSerializer()
    ownership = ClientOwnershipSerializer()
    classification = ClientClassificationSerializer()

    addresses = CompanyAddressSerializer(many=True)
    contacts = CompanyContactSerializer(many=True)

    class Meta:
        model = Client
        fields = '__all__'

    #  ADD HERE (inside class)


    def to_internal_value(self, data):
        data = data.copy()

        try:
            if isinstance(data.get('billing'), str):
                data['billing'] = json.loads(data['billing'])

            if isinstance(data.get('ownership'), str):
                data['ownership'] = json.loads(data['ownership'])

            if isinstance(data.get('classification'), str):
                data['classification'] = json.loads(data['classification'])

            if isinstance(data.get('addresses'), str):
                data['addresses'] = json.loads(data['addresses'])

            if isinstance(data.get('contacts'), str):
                data['contacts'] = json.loads(data['contacts'])

        except Exception as e:
            raise serializers.ValidationError(f"Invalid JSON format: {str(e)}")

        return super().to_internal_value(data)

    #  EXISTING CREATE METHOD
    def create(self, validated_data):
        billing_data = validated_data.pop('billing')
        ownership_data = validated_data.pop('ownership')
        classification_data = validated_data.pop('classification')
        addresses_data = validated_data.pop('addresses', [])
        contacts_data = validated_data.pop('contacts', [])

        signatures = self.context.get('signatures', {})

        client = Client.objects.create(**validated_data)

        ClientBilling.objects.create(client=client, **billing_data)
        ClientOwnership.objects.create(client=client, **ownership_data)
        ClientClassification.objects.create(client=client, **classification_data)

        for addr in addresses_data:
            CompanyAddress.objects.create(client=client, **addr)

        for index, contact in enumerate(contacts_data):
            sig = signatures.get(f'contact_signature_{index}')
            contact_obj = CompanyContact.objects.create(client=client, **contact)
            if sig:
                contact_obj.digital_signature = sig
                contact_obj.save()

        return client


# ==============================
# CAMPAIGN SERIALIZERS
# ==============================

class CreativeSerializer(serializers.ModelSerializer):
    main_asset_url = serializers.SerializerMethodField()
    #backup_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Creative
        fields = [
            'id',
            'line_item',
            'creative_name',

            'main_asset',
            'main_asset_url',

            #'backup_image',
            #'backup_image_url',

            'dimensions',
            'aspect_ratio',
            'file_size',

            'click_through_url',
            'appended_html_tag',
            'integration_code',
            'notes',
            'uploaded_at',
        ]

        read_only_fields = [
            'uploaded_at',
            'main_asset_url',
        ]

    def get_main_asset_url(self, obj):
        request = self.context.get('request')

        if obj.main_asset and request:
            return request.build_absolute_uri(obj.main_asset.url)

        return None

  

# ==============================
# THIRD PARTY CREATIVE
# ==============================

class ThirdPartyCreativeSerializer(serializers.ModelSerializer):

    input_file_url = serializers.SerializerMethodField()
    backup_image_url = serializers.SerializerMethodField()

    class Meta:
        model = ThirdPartyCreative

        fields = [
            'id',
            'line_item',
            'input_file',
            'input_file_url',
            'backup_image',
            'backup_image_url',
            'uploaded_at',
        ]

        read_only_fields = [
            'uploaded_at',
            'input_file_url',
            'backup_image_url',
        ]

    def get_input_file_url(self, obj):

        request = self.context.get('request')

        if obj.input_file and request:
            return request.build_absolute_uri(obj.input_file.url)

        return None

    def get_backup_image_url(self, obj):

        request = self.context.get('request')

        if obj.backup_image and request:
            return request.build_absolute_uri(obj.backup_image.url)

        return None


# ==============================
# LINE ITEM
# ==============================

class LineItemSerializer(serializers.ModelSerializer):
    creatives = CreativeSerializer(
        many=True,
        read_only=True,
        source='creatives_detail'  
    )

    third_party_creatives = ThirdPartyCreativeSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = LineItem
        fields = '__all__'


# ==============================
# CAMPAIGN
# ==============================

class CampaignSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)

    line_items = LineItemSerializer(many=True,read_only=True)

    client = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ['campaign_id']


    