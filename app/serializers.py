'''
from rest_framework import serializers
from .models import *


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


class ClientSerializer(serializers.ModelSerializer):
    billing = ClientBillingSerializer(source='clientbilling')
    #operational = ClientOperationalSerializer(source='clientoperational')
    ownership = ClientOwnershipSerializer(source='clientownership')
    classification = ClientClassificationSerializer(source='clientclassification')

    class Meta:
        model = Client
        fields = '__all__'

    def create(self, validated_data):
        billing_data = validated_data.pop('clientbilling')
        operational_data = validated_data.pop('clientoperational')
        ownership_data = validated_data.pop('clientownership')
        classification_data = validated_data.pop('clientclassification')

        client = Client.objects.create(**validated_data)

        ClientBilling.objects.create(client=client, **billing_data)
        #ClientOperational.objects.create(client=client, **operational_data)
        ClientOwnership.objects.create(client=client, **ownership_data)
        ClientClassification.objects.create(client=client, **classification_data)

        return client
    

class CampaignSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'

        '''



from rest_framework import serializers
from .models import *


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


# ✅ NEW: Address Serializer (MULTIPLE)
class CompanyAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAddress
        exclude = ['client']


# ✅ NEW: Contact Serializer (MULTIPLE)
class CompanyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyContact
        exclude = ['client']


# ==============================
# MAIN CLIENT SERIALIZER
# ==============================

class ClientSerializer(serializers.ModelSerializer):

    # One-to-one
    billing = ClientBillingSerializer(source='clientbilling')
    ownership = ClientOwnershipSerializer(source='clientownership')
    classification = ClientClassificationSerializer(source='clientclassification')

    # One-to-many (MULTIPLE)
    addresses = CompanyAddressSerializer(many=True)
    contacts = CompanyContactSerializer(many=True)

    class Meta:
        model = Client
        fields = '__all__'

    def create(self, validated_data):

        # Extract nested data
        billing_data = validated_data.pop('clientbilling')
        ownership_data = validated_data.pop('clientownership')
        classification_data = validated_data.pop('clientclassification')

        addresses_data = validated_data.pop('addresses', [])
        contacts_data = validated_data.pop('contacts', [])

        # Create main client
        client = Client.objects.create(**validated_data)

        # Create One-to-One
        ClientBilling.objects.create(client=client, **billing_data)
        ClientOwnership.objects.create(client=client, **ownership_data)
        ClientClassification.objects.create(client=client, **classification_data)

        # ✅ Create MULTIPLE addresses
        for addr in addresses_data:
            CompanyAddress.objects.create(client=client, **addr)

        # ✅ Create MULTIPLE contacts
        for contact in contacts_data:
            CompanyContact.objects.create(client=client, **contact)

        return client


# ==============================
# CAMPAIGN
# ==============================

class CampaignSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    campaign_id = serializers.CharField(read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'