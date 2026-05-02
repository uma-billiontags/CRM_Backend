'''
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import ClientSerializer, CampaignSerializer
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models import Sum
from django.utils.timezone import now


# Create your views here.

def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")


@api_view(['POST'])
def create_client(request):
    serializer = ClientSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Client created successfully"}, status=201)

    return Response(serializer.errors, status=400)


@api_view(['GET'])
def get_client(request, client_id):
    try:
        client = Client.objects.select_related(
            'clientbilling',
            'clientoperational',
            'clientownership',
            'clientclassification'
        ).get(client_id=client_id)

    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=404)

    serializer = ClientSerializer(client)
    return Response(serializer.data)


@api_view(['GET'])
def get_all_clients(request):
    clients = Client.objects.select_related(
        'clientbilling',
        'clientoperational',
        'clientownership',
        'clientclassification'
    ).all()

    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)



@api_view(['POST'])
def create_campaign(request):
    client_name = request.data.get('client_name') or request.data.get('client')
    
    if not client_name:
        return Response({"error": "client_name is required"}, status=400)
    
    try:
        client = Client.objects.get(name=client_name)
    except Client.DoesNotExist:
        return Response({"error": f"Client '{client_name}' not found"}, status=404)
    
    data = request.data.copy()
    data['client'] = client.id  # pass the actual PK to the serializer
    
    serializer = CampaignSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Campaign created successfully",
            "data": serializer.data
        }, status=201)
    return Response(serializer.errors, status=400)




# Fetch the campaign data

@api_view(['GET'])
def get_campaigns(request):

    campaigns = Campaign.objects.all()
    serializer = CampaignSerializer(campaigns, many=True)

    return Response(serializer.data)


# Fetch the campaign data based on client id
@api_view(['GET'])
def get_campaigns_by_client(request, client_id):

    campaigns = Campaign.objects.filter(client_id=client_id)
    serializer = CampaignSerializer(campaigns, many=True)

    return Response(serializer.data)
'''


from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Client, Campaign
from .serializers import ClientSerializer, CampaignSerializer


# Home
def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")


# ==============================
# CREATE CLIENT
# ==============================
@api_view(['POST'])
def create_client(request):
    serializer = ClientSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Client created successfully"}, status=201)

    return Response(serializer.errors, status=400)


# ==============================
# GET SINGLE CLIENT
# ==============================
@api_view(['GET'])
def get_client(request, client_id):
    try:
        client = Client.objects.select_related(
            'clientbilling',
            'clientownership',
            'clientclassification'
        ).prefetch_related(
            'addresses',   # 🔥 multiple addresses
            'contacts'     # 🔥 multiple contacts
        ).get(client_id=client_id)

    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=404)

    serializer = ClientSerializer(client)
    return Response(serializer.data)


# ==============================
# GET ALL CLIENTS
# ==============================
@api_view(['GET'])
def get_all_clients(request):
    clients = Client.objects.select_related(
        'clientbilling',
        'clientownership',
        'clientclassification'
    ).prefetch_related(
        'addresses',
        'contacts'
    ).all()

    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)


# ==============================
# CREATE CAMPAIGN
# ==============================
# @api_view(['POST'])
# def create_campaign(request):

#     client_id = request.data.get('client')

#     if not client_id:
#         return Response({"error": "client is required"}, status=400)

#     try:
#         client = Client.objects.get(id=client_id)
#     except Client.DoesNotExist:
#         return Response({"error": "Invalid client"}, status=404)

#     serializer = CampaignSerializer(data=request.data)

#     if serializer.is_valid():
#         serializer.save(client=client)   
#         return Response({
#     "message": "Campaign created successfully",
#     "campaign_id": serializer.instance.campaign_id,  # 👈 ADD THIS LINE
#     "data": serializer.data
# }, status=201)

#     return Response(serializer.errors, status=400)

@api_view(['POST'])
def create_campaign(request):
    client_id = request.data.get('client')
    if not client_id:
        return Response({"error": "client is required"}, status=400)

    try:
        #client = Client.objects.get(client_id=client_id)
        client = Client.objects.get(pk=client_id)  # ✅ fixed
    except Client.DoesNotExist:
        return Response({"error": "Invalid client"}, status=404)

    serializer = CampaignSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(client=client)
        return Response({
            "message": "Campaign created successfully",
            "campaign_id": serializer.instance.campaign_id,
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# ==============================
# GET ALL CAMPAIGNS
# ==============================
@api_view(['GET'])
def get_campaigns(request):
    campaigns = Campaign.objects.select_related('client').all()
    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)

# ==============================
# GET CAMPAIGNS BY CLIENT
# ==============================
@api_view(['GET'])
def get_campaigns_by_client(request, client_id):

    campaigns = Campaign.objects.filter(client_id=client_id).select_related('client')
    serializer = CampaignSerializer(campaigns, many=True)

    return Response(serializer.data)

@api_view(['GET'])
def get_campaign_by_id(request, campaign_id):

    try:
        campaign = Campaign.objects.select_related('client').get(campaign_id=campaign_id)
    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    serializer = CampaignSerializer(campaign)
    return Response(serializer.data)




