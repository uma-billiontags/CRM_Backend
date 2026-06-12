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

