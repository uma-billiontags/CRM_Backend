from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Client, Campaign
from .serializers import CustomerSerializer, ClientSerializer, CampaignSerializer
from django.contrib.auth.hashers import check_password

# Create your views here.

def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")



@api_view(['POST'])
def create_customer(request):
    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Customer created", "data": serializer.data})
    return Response(serializer.errors)



@api_view(['GET'])
def get_customers(request):
    customers = Customer.objects.all()

    if not customers.exists():
        return Response({
            "status": "success",
            "message": "No customers found",
            "data": []
        }, status=status.HTTP_200_OK)

    serializer = CustomerSerializer(customers, many=True)

    return Response({
        "status": "success",
        "message": "Customers fetched successfully",
        "data": serializer.data
    }, status=status.HTTP_200_OK)



# ONBOARD FORM FUNCTION

@api_view(['POST'])
def create_client(request):
    serializer = ClientSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()  # triggers save() → client_id + password hashing
        return Response({
            "status": True,
            "message": "Client Created Successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    print(serializer.errors)

    return Response({
        "status": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_clients(request):
    clients = Client.objects.all().order_by('-id')
    serializer = ClientSerializer(clients, many=True)

    return Response({
        "status": True,
        "data": serializer.data
    })


@api_view(['POST'])
def login_view(request):
    email = request.data.get('user_email')
    password = request.data.get('user_password')

    try:
        user = Client.objects.get(user_email=email)

        if check_password(password, user.user_password):
            return Response({
                "status": True,
                "message": "Login Success",
                "client_id": user.client_id,
                "client_name": user.client_name
            }, status=200)
        else:
            return Response({
                "status": False,
                "message": "Invalid Password"
            }, status=401)

    except Client.DoesNotExist:
        return Response({
            "status": False,
            "message": "Invalid Email"
        }, status=404)
    


# Campaign 
@api_view(['POST'])
def create_campaign(request):
    serializer = CampaignSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True})
    return Response(serializer.errors, status=400)


@api_view(['GET'])
def get_campaigns(request):
    campaigns = Campaign.objects.all()
    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)