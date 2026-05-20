# ----- Import libraries ------

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response 
from rest_framework import status
from .models import Client, Campaign,LineItem,Creative, ThirdPartyCreative, SuperAdmin
from .serializers import ClientSerializer, CampaignSerializer
import json
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Prefetch
from django.db import transaction  # imports Django transaction management system.
from datetime import datetime
from django.contrib.auth.hashers import make_password

# ==============================
# Home function 
# ==============================
def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")

# ==============================
# DEFINE CLIENT FUNCTION
# ==============================


# @api_view(['POST'])
# def create_client(request):
#     signatures = {
#         key: request.FILES[key]
#         for key in request.FILES
#         if key.startswith('contact_signature_')
#     }

#     # Unwrap JSON from FormData "data" field
#     raw = request.data.get('data')
#     if raw:
#         parsed = json.loads(raw)
#         data = parsed
#     else:
#         data = request.data

#     serializer = ClientSerializer(
#         data=data,
#         context={'signatures': signatures}
#     )
#     if serializer.is_valid():
#         serializer.save()
#         return Response({"message": "Client created successfully"}, status=201)
#     return Response(serializer.errors, status=400)



# ---------- client function ---------------


@api_view(['POST'])
def create_client(request):

    signatures = {

        key: request.FILES[key]

        for key in request.FILES

        if key.startswith(
            'contact_signature_'
        )
    }

    # Unwrap JSON from FormData
    raw = request.data.get('data')

    if raw:

        parsed = json.loads(raw)

        data = parsed

    else:

        data = request.data

    serializer = ClientSerializer(

        data=data,

        context={
            'signatures': signatures
        }
    )

    # =========================================
    # VALIDATION
    # =========================================

    if serializer.is_valid():

        # Save client
        client = serializer.save()

        # =====================================
        # GET EMAIL FROM CLIENT
        # =====================================

        email = client.email

        # =====================================
        # CREATE USER LOGIN
        # =====================================

        if email and not User.objects.filter(
            email=email
        ).exists():

            user = User.objects.create(

                username=email,

                email=email,

                role='client',

                client=client  # links every user with their own Client object.
            )

            # Default password
            user.set_password("123")

            user.save()

        return Response({

            "message":
            "Client created successfully",

            "default_password":
            "123"

        }, status=201)

    return Response(
        serializer.errors,
        status=400
    )




# ==============================
# GET SINGLE CLIENT
# ==============================
@api_view(['GET'])
def get_client(request, client_id):
    try:
        client = Client.objects.select_related(
            'billing',          #  FIXED
            'ownership',        #  FIXED
            'classification'    #  FIXED
        ).prefetch_related(
            'addresses',        # correct
            'contacts'          # correct
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
        'billing',          # FIXED
        'ownership',        #  FIXED
        'classification'    #  FIXED
    ).prefetch_related(
        'addresses',        #  correct
        'contacts'          #  correct
    ).all()

    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)


# ------------------------------------------------------------------------------------
# ==============================
# CREATE CAMPAIGN
# ==============================

# Creates a custom function to convert frontend date string into Python date.
def parse_date(date_str):

    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace('Z', '')).date()


@api_view(['POST']) 
@parser_classes([MultiPartParser, FormParser])  # it allows file upload, formdata. (without this file uploads won't work)
def create_campaign(request):

    client_id = request.data.get('client') # get the client id CLT-2026-00001 from frontend
    if not client_id:
        return Response({"error": "client is required"},status=400) # if frontend not send throw this error

    # =====================================================
    # FIND CLIENT
    # =====================================================

    try:
        client = Client.objects.get(client_id=client_id) # find the client(full details) from database
    except Client.DoesNotExist:
        return Response({"error": f"Client '{client_id}' not found"},status=404)

    # =====================================================
    # VALIDATE CAMPAIGN
    # =====================================================

    serializer = CampaignSerializer(data=request.data) # Take all data coming from frontend request and give it to serializer.
    if not serializer.is_valid():
        return Response(serializer.errors,status=400)

    try:
        with transaction.atomic(): # save together
            campaign = serializer.save(client=client) # save campagin

            try:
                line_items_data = json.loads(request.data.get('line_items','[]')) # get the line items from frontend and converts json into python dict
            except Exception:
                return Response({"error": "Invalid line_items JSON"},status=400)

            # =============================================
            # LOOP LINE ITEMS
            # =============================================

            for i, li in enumerate(line_items_data): # Loop through every line item one by one. (eg: i=0, li=first line item)

                line_item_id = li.get('line_item_id') # get the line item id (LIUSER0001)

                if not line_item_id:   # If no ID, skip that line item.
                    continue

                line_item, _ = LineItem.objects.update_or_create(  # Search LineItem using line_item_id (if line item data already exist (update) or (create))
                    line_item_id=line_item_id,
                    defaults={

                        'campaign': campaign,
                        'line_item_name': li.get('lineItemName'),
                        'ethnicity': li.get('ethnicity',[]),
                        'start_date': parse_date(li.get('startDate')),
                        'end_date': parse_date(li.get('endDate')),
                        'ad_format': li.get('adFormat',[]),
                        'impressions': li.get('impressions') or None,
                        'units': li.get('units') or None,
                        'ctr': li.get('ctr') or None,
                        'viewability': li.get('viewability') or None,
                        'vcr': li.get('vcr') or None,
                        'unit_cost': li.get('unit_cost') or None,
                        'kpi_notes': li.get('kpi_notes', ''),
                        'unit_value': li.get('unit_value') or None,

                    }
                )

        
                # Fix — two separate loops

                # Loop 1: normal creatives
                creatives_meta = li.get('creatives', [])
                for j, meta in enumerate(creatives_meta):
                    if not meta.get('creative_name'):
                        continue

                    main_asset = request.FILES.get(f'line_item_{i}main_asset{j}')
                    Creative.objects.create(
                        line_item=line_item,
                        creative_name=meta.get('creative_name', ''),
                        main_asset=main_asset,
                        dimensions=meta.get('dimensions', ''),
                        aspect_ratio=meta.get('aspect_ratio', ''),
                        file_size=meta.get('file_size', ''),
                        click_through_url=meta.get('click_through_url') or None,
                        appended_html_tag=meta.get('appended_html_tag', ''),
                        integration_code=meta.get('integration_code', ''),
                        notes=meta.get('notes', ''),
                    )

                # Loop 2: third-party creatives — completely separate
                third_party_meta = li.get('third_party_creatives', [])
                for k, _ in enumerate(third_party_meta):
                    input_file = request.FILES.get(f'line_item_{i}thirdparty_file{k}')
                    backup_image = request.FILES.get(f'line_item_{i}thirdparty_backup{k}')
                    ThirdPartyCreative.objects.create(
                        line_item=line_item,
                        input_file=input_file,
                        backup_image=backup_image,
                    )
                
    except Exception as e:
        return Response({"error": str(e)},status=500)

    return Response({"message": (
            "Campaign + LineItem + "
            "Creative + ThirdPartyCreative "
            "saved successfully"
        ),
        "campaign_id": campaign.campaign_id,}, status=201)



#===========================
# GET ALL CAMPAIGNS
# ==========================

@api_view(['GET'])
def get_campaigns(request):

    campaigns = Campaign.objects.select_related('client').prefetch_related(
        'line_items__creatives_detail',
        'line_items__third_party_creatives' 
    )
    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)


# ==============================
# GET CAMPAIGNS BY CLIENT ID
# ==============================
    
@api_view(['GET'])
def get_campaigns_by_client(request, client_id):  # http://127.0.0.1:8000/get_campaigns_by_client/CLT-2026-00001/

    try:
        campaigns = Campaign.objects.filter(
            client__client_id=client_id
        ).select_related('client').prefetch_related(
            Prefetch(
                'line_items',
                queryset=LineItem.objects.prefetch_related('creatives_detail')
            )
        )

        if not campaigns.exists():
            return Response({"message": "No campaigns found for this client"}, status=404)

        serializer = CampaignSerializer(campaigns, many=True) 
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ==============================
# GET CAMPAIGNS BY CAMPAIGN ID
# ==============================

@api_view(['GET'])
def get_campaign_by_id(request, campaign_id):  # http://127.0.0.1:8000/get_campaign_by_id/CMP-2026-00001/

    try:
        campaign = Campaign.objects.select_related('client').prefetch_related(
            Prefetch(
                'line_items',
                queryset=LineItem.objects.prefetch_related('creatives_detail')
            )
        ).get(campaign_id=campaign_id)

    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    serializer = CampaignSerializer(campaign)
    return Response(serializer.data)


# -------------------------------------------------

# =========================================================
# UPDATE CAMPAIGN
# =========================================================

@api_view(['GET', 'PUT'])
@parser_classes([MultiPartParser, FormParser])

def update_campaign(request, campaign_id):

    # =====================================================
    # FIND EXISTING CAMPAIGN
    # =====================================================

    try:

        campaign = Campaign.objects.select_related(
            'client'
        ).prefetch_related(
            'line_items__creatives_detail',
            'line_items__third_party_creatives'
        ).get(
            campaign_id=campaign_id
        )

    except Campaign.DoesNotExist:

        return Response(
            {"error": "Campaign not found"},
            status=404
        )

    # =====================================================
    # GET EXISTING DATA
    # =====================================================

    if request.method == 'GET':

        serializer = CampaignSerializer(
            campaign,
            context={'request': request}
        )

        return Response(serializer.data)

    # =====================================================
    # UPDATE DATA
    # =====================================================

    try:

        with transaction.atomic():

            # =============================================
            # UPDATE CAMPAIGN DETAILS
            # =============================================

            serializer = CampaignSerializer(
                campaign,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():

                return Response(
                    serializer.errors,
                    status=400
                )

            serializer.save()

            # =============================================
            # GET LINE ITEMS
            # =============================================

            try:

                line_items_data = json.loads(
                    request.data.get(
                        'line_items',
                        '[]'
                    )
                )

            except Exception:

                return Response(
                    {"error": "Invalid line_items JSON"},
                    status=400
                )

            # =============================================
            # LOOP LINE ITEMS
            # =============================================

            for i, li in enumerate(line_items_data):

                line_item_id = li.get(
                    'line_item_id'
                )

                if not line_item_id:
                    continue

                # =========================================
                # UPDATE / CREATE LINE ITEM
                # =========================================

                line_item, _ = LineItem.objects.update_or_create(

                    line_item_id=line_item_id,

                    defaults={

                        'campaign': campaign,
                        'line_item_name': li.get('lineItemName'),
                        'ethnicity': li.get('ethnicity',[]),
                        'start_date': parse_date(li.get('startDate')),
                        'end_date': parse_date(li.get('endDate')),
                        'ad_format': li.get('adFormat',[]),
                        'impressions': li.get('impressions') or None,
                        'units': li.get('units') or None,
                        'ctr': li.get('ctr') or None,
                        'viewability': li.get('viewability') or None,
                        'vcr': li.get('vcr') or None,
                        'unit_cost': li.get('unit_cost') or None,
                        'kpi_notes': li.get('kpi_notes', ''),
                        'unit_value': li.get('unit_value') or None,

                    }
                )

                # =========================================
                # NORMAL CREATIVES
                # =========================================

                creatives_meta = li.get(
                    'creatives',
                    []
                )

                for j, meta in enumerate(creatives_meta):

                    if not meta.get(
                        'creative_name'
                    ):
                        continue

                    main_asset = request.FILES.get(
                        f'line_item_{i}main_asset{j}'
                    )

                    Creative.objects.create(

                        line_item=line_item,

                        creative_name=meta.get(
                            'creative_name',
                            ''
                        ),

                        main_asset=main_asset,

                        dimensions=meta.get(
                            'dimensions',
                            ''
                        ),

                        aspect_ratio=meta.get(
                            'aspect_ratio',
                            ''
                        ),

                        file_size=meta.get(
                            'file_size',
                            ''
                        ),

                        click_through_url=meta.get(
                            'click_through_url'
                        ) or None,

                        appended_html_tag=meta.get(
                            'appended_html_tag',
                            ''
                        ),

                        integration_code=meta.get(
                            'integration_code',
                            ''
                        ),

                        notes=meta.get(
                            'notes',
                            ''
                        ),
                    )

                # =========================================
                # THIRD PARTY CREATIVES
                # =========================================

                third_party_meta = li.get(
                    'third_party_creatives',
                    []
                )

                for k, _ in enumerate(third_party_meta):

                    input_file = request.FILES.get(
                        f'line_item_{i}thirdparty_file{k}'
                    )

                    backup_image = request.FILES.get(
                        f'line_item_{i}thirdparty_backup{k}'
                    )

                    ThirdPartyCreative.objects.create(

                        line_item=line_item,

                        input_file=input_file,

                        backup_image=backup_image,
                    )

    except Exception as e:

        return Response(
            {"error": str(e)},
            status=500
        )

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================

    return Response({

        "message": "Campaign updated successfully",

        "campaign_id": campaign.campaign_id,

    }, status=200) 

# ------------- Login functionality ---------------

from django.contrib.auth import authenticate
from app.models import User

# @api_view(['POST'])
# def login_view(request):

#     email = request.data.get('email')
#     password = request.data.get('password')

#     try:
#         user_obj = User.objects.get(email=email)

#     except User.DoesNotExist:

#         return Response({"error": "Invalid email"},status=401)

#     user = authenticate(
#         username=user_obj.username,
#         password=password
#     )
#     if user is None:
#         return Response({"error": "Invalid password"},status=401)

#     return Response({
#         "message": "Login successful",

#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "role": user.role,   
#             "client_id": user.client.client_id if user.client else None, 
#         }

#     }, status=200)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SuperAdmin


@api_view(['POST'])
def login_view(request):

    # =====================================
    # GET DATA
    # =====================================

    email = request.data.get('email')

    password = request.data.get('password')

    # =====================================
    # VALIDATION
    # =====================================

    if not email or not password:

        return Response({

            "error":
            "Email and password are required"

        }, status=400)

    # =====================================
    # FIND APPROVED CLIENT
    # =====================================

    try:

        approval = SuperAdmin.objects.select_related(
            'client'
        ).get(

            client__email=email,

            approval_status='approved'
        )

    except SuperAdmin.DoesNotExist:

        return Response({

            "error":
            "Account not approved or email not found"

        }, status=401)

    # =====================================
    # CHECK PASSWORD
    # =====================================

    if approval.client_password != password:

        return Response({

            "error":
            "Invalid password"

        }, status=401)

    # =====================================
    # SUCCESS RESPONSE
    # =====================================

    return Response({

        "message": "Login successful",

        "client": {

            "client_id":
            approval.client.client_id,

            "company_name":
            approval.client.name,

            "email":
            approval.client.email,

            "approval_status":
            approval.approval_status,
        }

    }, status=200)





# ------------------ Download function ----------------------

from django.http import FileResponse
from django.shortcuts import get_object_or_404


@api_view(['GET'])
def download_creative(request, creative_id):

    # Get creative object
    creative = get_object_or_404(Creative,id=creative_id)

    # Get uploaded file path
    file_path = creative.main_asset.path

    # Return downloadable response
    return FileResponse(open(file_path, 'rb'),as_attachment=True,filename=creative.main_asset.name) 


# Third party function
@api_view(['GET'])
def download_thirdparty(request,thirdparty_id):

    # Get third-party creative object
    thirdparty = get_object_or_404(ThirdPartyCreative,id=thirdparty_id)

    if not thirdparty.input_file:
        return Response({"error":"No input file uploaded"},status=404)

    # Get uploaded file path
    file_path = thirdparty.input_file.path

    # Return downloadable response
    return FileResponse(open(file_path, 'rb'),as_attachment=True,filename=thirdparty.input_file.name)


# Backup image function
@api_view(['GET'])
def download_backup_image(request,thirdparty_id):

    thirdparty = get_object_or_404(ThirdPartyCreative,id=thirdparty_id)

    if not thirdparty.backup_image:
        return Response({"error":"No input file uploaded"},status=404)
    file_path = thirdparty.backup_image.path
    return FileResponse(open(file_path, 'rb'),as_attachment=True,filename=thirdparty.backup_image.name)


# ===================================
# Write the logic for superadmin function

from .serializers import SuperAdminSerializer

from django.core.mail import send_mail

from django.utils import timezone


# ==============================
# GET ALL CLIENTS FOR APPROVAL
# ==============================

@api_view(['GET'])
def get_clients_for_approval(request):

    clients = Client.objects.all().order_by(
        '-created_at'
    )

    data = []

    for client in clients:

        approval = SuperAdmin.objects.filter(
            client=client
        ).first()

        data.append({

            "client_id": client.client_id,

            "company_name": client.name,

            "email": client.email,

            "phone": client.phone,

            "approval_status":

                approval.approval_status

                if approval else "pending"
        })

    return Response(data)


# ==============================
# APPROVE CLIENT
# ==============================

@api_view(['POST'])
def approve_client(request):

    client_id = request.data.get(
        'client_id'
    )

    password = request.data.get(
        'password'
    )

    # =====================================
    # VALIDATION
    # =====================================

    if not client_id or not password:

        return Response({

            "error":
            "client_id and password required"

        }, status=400)

    # =====================================
    # GET CLIENT
    # =====================================

    try:

        client = Client.objects.get(
            client_id=client_id
        )

    except Client.DoesNotExist:

        return Response({

            "error": "Client not found"

        }, status=404)

    # =====================================
    # SAVE APPROVAL
    # =====================================

    approval, created = SuperAdmin.objects.update_or_create(

        client=client,

        defaults={

            'approval_status': 'approved',

            'client_password': password,

            'email_sent': True,

            'approved_at': timezone.now()
        }
    )

    # =====================================
    # SEND EMAIL
    # =====================================

    send_mail(

        subject='CRM Login Credentials',

        message=f'''
Hello {client.name},

Your CRM account has been approved.

Login Email:
{client.email}

Password:
{password}

You can now login and create campaigns.

Thank You
''',

        from_email='yourgmail@gmail.com',

        recipient_list=[client.email],

        fail_silently=False
    )

    # =====================================
    # RESPONSE
    # =====================================

    serializer = SuperAdminSerializer(
        approval
    )

    return Response({

        "message":
        "Client approved successfully",

        "data":
        serializer.data

    }, status=200)


# ==============================
# GET APPROVAL DETAILS
# ==============================

@api_view(['GET'])
def get_approval_details(request, client_id):

    try:

        approval = SuperAdmin.objects.select_related(
            'client'
        ).get(
            client__client_id=client_id
        )

    except SuperAdmin.DoesNotExist:

        return Response({

            "error": "Approval details not found"

        }, status=404)

    serializer = SuperAdminSerializer(
        approval
    )

    return Response(serializer.data)