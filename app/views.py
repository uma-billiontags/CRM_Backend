# ----- Import libraries ------

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response 
from rest_framework import status
from .models import Client, Campaign,LineItem,Creative, ThirdPartyCreative
from .serializers import ClientSerializer, CampaignSerializer, CreativeSerializer
import json
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Prefetch
from django.db import transaction  # imports Django transaction management system.
from datetime import datetime


# Home
def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")

# ==============================
# DEFINE CLIENT FUNCTION
# ==============================
@api_view(['POST'])
def create_client(request):
    signatures = {
        key: request.FILES[key]
        for key in request.FILES
        if key.startswith('contact_signature_')
    }

    # Unwrap JSON from FormData "data" field
    raw = request.data.get('data')
    if raw:
        parsed = json.loads(raw)
        data = parsed
    else:
        data = request.data

    serializer = ClientSerializer(
        data=data,
        context={'signatures': signatures}
    )
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

'''
# Creates a custom function to convert frontend date string into Python date.
def parse_date(date_str):
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace('Z', '')).date()


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser]) # it allows file upload, formdata. (without this file uploads won't work)
def create_campaign(request):

    client_id = request.data.get('client') # get the client id CLT-2026-00001 from frontend

    if not client_id:
        return Response({"error": "client is required"}, status=400) # if frontend not send throw this error

    try:
        client = Client.objects.get(client_id=client_id) # find the client(full details) from database
    except Client.DoesNotExist:
        return Response({"error": f"Client '{client_id}' not found"}, status=404)
    
    # Validate the campaign data
     
    serializer = CampaignSerializer(data=request.data) # Take all data coming from frontend request and give it to serializer.

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    try:
        with transaction.atomic(): # save all together (campaign, lineitem, creatives)

            campaign = serializer.save(client=client) # save campagin

            # IMPORTANT: JSON parse
            try:
                line_items_data = json.loads(request.data.get('line_items', '[]')) # get the line items from frontend and converts json into python dict
            except Exception:
                return Response({"error": "Invalid line_items JSON"}, status=400)

            for i, li in enumerate(line_items_data): # Loop through every line item one by one. (eg: i=0, li=first line item)

                line_item_id = li.get('line_item_id') # get the line item id (LIUSER0001)

                if not line_item_id: # If no ID, skip that line item.
                    continue

                #  FIX: store object
                line_item, _ = LineItem.objects.update_or_create(   # Search LineItem using line_item_id (if line item data already exist (update) or (create))
                    line_item_id=line_item_id,
                    defaults={                  # defaults is used for create and update
                        'campaign': campaign,
                        'line_item_name': li.get('lineItemName'),
                        'ethnicity': li.get('ethnicity', []),
                        'start_date': parse_date(li.get('startDate')),
                        'end_date': parse_date(li.get('endDate')),
                        'ad_format': li.get('adFormat', []),
                        'impressions': li.get('impressions') or None,
                        #'landing_page': li.get('landingPage') or None,
                        'units': li.get('units') or None,
                        'ctr': li.get('ctr') or None,
                        'viewability': li.get('viewability') or None,
                        'vcr': li.get('vcr') or None,
                    }
                )

                # creatives must come from frontend
                creatives_meta = li.get('creatives', []) 
                
                # loop all creatives
                for j, meta in enumerate(creatives_meta): # (j=0 and meta=first creative)

                    # validate the creative name
                    if not meta.get('creative_name'):
                        continue

                    #  File upload (request file from frontend)
                    main_asset = request.FILES.get(f'line_item_{i}main_asset{j}')
                    #backup_image = request.FILES.get(f'line_item_{i}backup_image{j}')

                    Creative.objects.create(
                        line_item=line_item,
                        creative_name=meta.get('creative_name', ''),
                        main_asset=main_asset,
                        #backup_image=backup_image,
                        dimensions=meta.get('dimensions', ''),
                        aspect_ratio=meta.get('aspect_ratio', ''),
                        file_size=meta.get('file_size', ''),
                        click_through_url=meta.get('click_through_url') or None,
                        appended_html_tag=meta.get('appended_html_tag', ''),
                        integration_code=meta.get('integration_code', ''),
                        notes=meta.get('notes', ''),
                    )
                    
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    return Response({
        "message": "Campaign + LineItem + Creatives saved successfully",
        "campaign_id": campaign.campaign_id,
    }, status=201)

'''




# =========================================================
# CONVERT FRONTEND DATE STRING TO PYTHON DATE
#==========================================================



# =========================================================
# DATE PARSER
# =========================================================

def parse_date(date_str):

    if not date_str:
        return None

    return datetime.fromisoformat(
        date_str.replace('Z', '')
    ).date()


# =========================================================
# CREATE CAMPAIGN
# =========================================================

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])

def create_campaign(request):

    # =====================================================
    # GET CLIENT ID
    # =====================================================

    client_id = request.data.get('client')

    if not client_id:

        return Response(
            {"error": "client is required"},
            status=400
        )

    # =====================================================
    # FIND CLIENT
    # =====================================================

    try:

        client = Client.objects.get(
            client_id=client_id
        )

    except Client.DoesNotExist:

        return Response(
            {"error": f"Client '{client_id}' not found"},
            status=404
        )

    # =====================================================
    # VALIDATE CAMPAIGN
    # =====================================================

    serializer = CampaignSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            serializer.errors,
            status=400
        )

    try:

        # =================================================
        # SAVE EVERYTHING INSIDE TRANSACTION
        # =================================================

        with transaction.atomic():

            # =============================================
            # SAVE CAMPAIGN
            # =============================================

            campaign = serializer.save(
                client=client
            )

            # =============================================
            # GET LINE ITEMS JSON
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
                # CREATE / UPDATE LINE ITEM
                # =========================================

                line_item, _ = LineItem.objects.update_or_create(

                    line_item_id=line_item_id,

                    defaults={

                        'campaign': campaign,

                        'line_item_name': li.get(
                            'lineItemName'
                        ),

                        'ethnicity': li.get(
                            'ethnicity',
                            []
                        ),

                        'start_date': parse_date(
                            li.get('startDate')
                        ),

                        'end_date': parse_date(
                            li.get('endDate')
                        ),

                        'ad_format': li.get(
                            'adFormat',
                            []
                        ),

                        'impressions': li.get(
                            'impressions'
                        ) or None,

                        'units': li.get(
                            'units'
                        ) or None,

                        'ctr': li.get(
                            'ctr'
                        ) or None,

                        'viewability': li.get(
                            'viewability'
                        ) or None,

                        'vcr': li.get(
                            'vcr'
                        ) or None,
                    }
                )

                # =========================================
                # GET CREATIVES
                # =========================================

                creatives_meta = li.get(
                    'creatives',
                    []
                )

                # =========================================
                # LOOP CREATIVES
                # =========================================

                for j, meta in enumerate(creatives_meta):

                    # =====================================
                    # THIRD PARTY CREATIVE
                    # =====================================

                    if meta.get('type') == 'third_party':

                        input_file = request.FILES.get(
                            f'line_item_{i}thirdparty_file{j}'
                        )

                        backup_image = request.FILES.get(
                            f'line_item_{i}thirdparty_backup{j}'
                        )

                        ThirdPartyCreative.objects.create(

                            line_item=line_item,

                            input_file=input_file,

                            backup_image=backup_image,
                        )

                    # =====================================
                    # NORMAL CREATIVE
                    # =====================================

                    else:

                        # Skip if no creative name
                        if not meta.get(
                            'creative_name'
                        ):
                            continue

                        # ===============================
                        # GET FILE
                        # ===============================

                        main_asset = request.FILES.get(
                            f'line_item_{i}main_asset{j}'
                        )

                        # ===============================
                        # SAVE CREATIVE
                        # ===============================

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

    except Exception as e:

        return Response(
            {"error": str(e)},
            status=500
        )

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================

    return Response({

        "message": (
            "Campaign + LineItem + "
            "Creative + ThirdPartyCreative "
            "saved successfully"
        ),

        "campaign_id": campaign.campaign_id,

    }, status=201)

#===========================
# GET ALL CAMPAIGNS
# ==========================

@api_view(['GET'])
def get_campaigns(request):

    campaigns = Campaign.objects.select_related('client').prefetch_related(
        'line_items__creatives_detail'
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

