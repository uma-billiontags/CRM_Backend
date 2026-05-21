# ----- Import libraries ------

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response 
from rest_framework import status
from .models import Client, Campaign,LineItem,Creative, ThirdPartyCreative, Client, User, TeamAccess
from .serializers import ClientSerializer, CampaignSerializer, TeamAccessSerializer
import json
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Prefetch
from django.db import transaction  # imports Django transaction management system.
from datetime import datetime
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from django.utils import timezone



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

    if serializer.is_valid():

        client = serializer.save()

        email = client.email

        # CREATE USER ONLY
        if email and not User.objects.filter(
            email=email
        ).exists():

            User.objects.create(

                username=email,

                email=email,

                role='client',

                client=client
            )

        return Response({

            "message":
            "Client created successfully"

        }, status=201)

    return Response(
        serializer.errors,
        status=400
    )


# To update the client function for approvel
@api_view(['PATCH'])
def update_client_status(request, client_id):
    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=404)

    status = request.data.get('status')
    if status not in ['pending', 'approved', 'rejected']:
        return Response({"error": "Invalid status"}, status=400)

    client.status = status
    client.save()
    return Response({"message": f"Client status updated to {status}"}, status=200)







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




# =========================================================
# DELETE CAMPAIGN
# =========================================================

@api_view(['DELETE'])
def delete_campaign(request, campaign_id):

    # =====================================================
    # FIND CAMPAIGN
    # =====================================================

    try:

        campaign = Campaign.objects.get(
            campaign_id=campaign_id
        )

    except Campaign.DoesNotExist:

        return Response({

            "error": "Campaign not found"

        }, status=404)

    # =====================================================
    # DELETE CAMPAIGN
    # =====================================================

    campaign.delete()

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================

    return Response({

        "message": "Campaign deleted successfully",

        "campaign_id": campaign_id

    }, status=200)

# ------------- Login functionality ---------------

# @api_view(['POST'])
# def login_view(request):

#     email = request.data.get('email') # get the email and password from frontend request body
#     password = request.data.get('password')
#     if not email or not password:
#         return Response({"error":"Email and password are required"}, status=400)

#     # FIND USER
#     try:
#         user_obj = User.objects.get(email=email) # searches the user in db using email
#     except User.DoesNotExist:
#         return Response({"error":"Invalid email"}, status=401)

#     # AUTHENTICATE
#     user = authenticate(  # verifies the password & username using django built-in authentication system.
#         username=user_obj.username,
#         password=password
#     )

#     if user is None:
#         return Response({"error":"Invalid password"}, status=401)
    
#     # UPDATE LAST LOGIN TIME
#     user.last_login = timezone.now()
#     user.save()

#     # CHECK CLIENT APPROVAL
#     if user.role == 'client':   # check if the logged user is client
#         if user.client.status != 'approved':  # check the client approvel status
#             return Response({"error":"Your account is not approved yet"}, status=403)

#     return Response({

#         "message": "Login successful",
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "role": user.role,
#             "client_id": (user.client.client_id if user.client else None)# If user linked with client: return client id otherwise return None # If user linked with client: return client id otherwise return None 
#         }
#     }, status=200)



@api_view(['POST'])
def login_view(request):
    email = request.data.get('email') # get the email and password from frontend request body
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=400) 

    # ── 1. Check TeamAccess table first (team members) ──────────────────────
    try:
        team_member = TeamAccess.objects.get(email=email)

        if team_member.status != 'Active':
            return Response({"error": "Your account is inactive. Contact your administrator."}, status=403)

        if team_member.password != password:
            return Response({"error": "Invalid password"}, status=401)

        return Response({
            "message": "Login successful",
            "user": {
                "id":        team_member.id,
                "username":  team_member.member,
                "email":     team_member.email,
                "role":      team_member.role,
                "client_id": None,
                "source":    "team",
            }
        }, status=200)

    except TeamAccess.DoesNotExist:
        pass  # not a team member, check user table next

    # ── 2. Check User table (clients + superadmin) ───────────────────────────
    try:
        user_obj = User.objects.get(email=email)   # searches the user in db using email
    except User.DoesNotExist:
        return Response({"error": "No account found with this email"}, status=401)

    user = authenticate(username=user_obj.username, password=password)   # verifies the password & username using django built-in authentication system
    if user is None:
        return Response({"error": "Invalid password"}, status=401)
    
    # UPDATE LAST LOGIN TIME    
    user.last_login = timezone.now()
    user.save()
    
    if user.role == 'client':   # check if the logged user is client
        if user.client is None or user.client.status != 'approved':      # check the client approvel status
            return Response({"error": "Your account is not approved yet"}, status=403)

    return Response({
        "message": "Login successful",
        "user": {
            "id":        user.id,
            "username":  user.username,
            "email":     user.email,
            "role":      user.role,
            "client_id": user.client.client_id if user.client else None,     # If user linked with client: return client id otherwise return None
            "source":    "user",
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


# ===============================
# APPROVAL FUNCTIONALITY
# ===============================
from django.core.mail import send_mail

@api_view(['POST'])
def approve_client(request):

    # =====================================
    # GET DATA FROM FRONTEND
    # =====================================

    client_id = request.data.get('client_id')

    password = request.data.get('password')

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

            "error":
            "Client not found"

        }, status=404)

    # =====================================
    # CREATE USER IF NOT EXISTS
    # =====================================

    user, created = User.objects.get_or_create(

        email=client.email,

        defaults={

            "username": client.client_id,

            "email": client.email,

            "role": "client",

            "client": client
        }
    )

    # =====================================
    # UPDATE USER DETAILS
    # =====================================

    user.username = client.email   # client.email  (or) client.client_id

    user.email = client.email

    user.role = "client"

    user.client = client

    # SET PASSWORD (HASH PASSWORD)
    user.set_password(password)

    # SAVE USER
    user.save()

    # =====================================
    # UPDATE CLIENT STATUS
    # =====================================

    client.status = "approved"

    client.save()

    # =====================================
    # SEND LOGIN EMAIL
    # =====================================

    send_mail(

        subject='CRM Login Credentials',

        message=f'''
Hello {client.name},

Your account has been approved.

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
    # SUCCESS RESPONSE
    # =====================================

    return Response({

        "message":
        "Client approved successfully",

        "client_id":
        client.client_id,

        "email":
        client.email,

        "status":
        client.status

    }, status=200)


# ---------------------------
# TEAM MEMBER MANAGEMENT
# ---------------------------

# Create Team Member
@api_view(['POST'])
def create_team_member(request):

    serializer = TeamAccessSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get All Team Members
@api_view(['GET'])
def get_team_members(request):

    members = TeamAccess.objects.all().order_by('-id')
    serializer = TeamAccessSerializer(members, many=True)

    return Response(serializer.data)


# Edit Team Member
@api_view(['PUT'])
def edit_team_member(request, id):

    try:
        member = TeamAccess.objects.get(id=id)
    except TeamAccess.DoesNotExist:
        return Response(
            {"error": "Team member not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = TeamAccessSerializer(member, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete Team Member
@api_view(['DELETE'])
def delete_team_member(request, id):

    try:
        member = TeamAccess.objects.get(id=id)
    except TeamAccess.DoesNotExist:
        return Response(
            {"error": "Team member not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    member.delete()

    return Response(
        {"message": "Team member deleted successfully"},
        status=status.HTTP_200_OK
    )


# ---------------------------
# USER MANAGEMENT
# ---------------------------

# GET all client users
@api_view(['GET'])
def get_client_users(request):
    users = User.objects.filter(role='client').select_related('client')
    data = []
    for u in users:
        data.append({
            "id": u.id,
            "client_id": u.client.client_id if u.client else u.username,
            "email": u.email,
            "role": u.role,
            "status": getattr(u, 'status', 'Active'),  # once you add status field
            "last_active": u.last_login.isoformat() if u.last_login else u.date_joined.isoformat(),
        })
    return Response(data)

# @api_view(['DELETE'])
# def delete_client_user(request, id):
#     try:
#         user = User.objects.get(id=id, role='client')
#     except User.DoesNotExist:
#         return Response({"error": "Client user not found"}, status=404)
#     user.delete()
#     return Response({"message": "Deleted successfully"}, status=200)



@api_view(['DELETE'])
def delete_client_user(request, id):

    # =====================================
    # FIND CLIENT USER
    # =====================================

    try:

        user = User.objects.select_related(
            'client'
        ).get(

            id=id,

            role='client'
        )

    except User.DoesNotExist:

        return Response({

            "error":
            "Client user not found"

        }, status=404)

    # =====================================
    # STORE DETAILS
    # =====================================

    client = user.client

    deleted_data = {

        "user_id": user.id,

        "email": user.email,

        "client_id": (

            client.client_id
            if client else None
        )
    }

    # =====================================
    # DELETE CLIENT TABLE
    # =====================================

    if client:

        client.delete()

    # =====================================
    # SUCCESS RESPONSE
    # =====================================

    return Response({

        "message":
        "Client and user deleted successfully",

        "deleted_data":
        deleted_data

    }, status=200)


@api_view(['PUT'])
def edit_client_user(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    password = request.data.get('password')
    status = request.data.get('status')

    if password:
        user.set_password(password)
    if status:
        user.status = status   # add this field to User model first

    user.save()
    return Response({"message": "Updated successfully"}, status=200)