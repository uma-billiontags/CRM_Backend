# ----- Import libraries ------

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Client, Campaign,LineItem,Creative
from .serializers import ClientSerializer, CampaignSerializer, CreativeSerializer
import json
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Prefetch
from django.db import transaction
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

# def parse_date(date_str):
#     if not date_str:
#         return None
#     return datetime.fromisoformat(date_str.replace('Z', '')).date()


# @api_view(['POST'])
# @parser_classes([MultiPartParser, FormParser])
# def create_campaign(request):

#     client_id = request.data.get('client')

#     if not client_id:
#         return Response({"error": "client is required"}, status=400)

#     try:
#         client = Client.objects.get(client_id=client_id)
#     except Client.DoesNotExist:
#         return Response({"error": f"Client '{client_id}' not found"}, status=404)

#     serializer = CampaignSerializer(data=request.data)

#     if not serializer.is_valid():
#         return Response(serializer.errors, status=400)

#     try:
#         with transaction.atomic():

#             campaign = serializer.save(client=client)

#             try:
#                 line_items_data = json.loads(request.data.get('line_items', '[]'))
#             except Exception:
#                 return Response({"error": "Invalid line_items JSON"}, status=400)

#             for i, li in enumerate(line_items_data):

#                 line_item_id = li.get('line_item_id')

#                 if not line_item_id:
#                     continue

#                 if not li.get('lineItemName'):
#                     return Response({"error": "lineItemName is required"}, status=400)

#                 line_item, _ = LineItem.objects.update_or_create(
#                     line_item_id=line_item_id,
#                     defaults={
#                         'campaign': campaign,
#                         'line_item_name': li.get('lineItemName'),
#                         'ethnicity': li.get('ethnicity', []),
#                         'start_date': parse_date(li.get('startDate')),
#                         'end_date': parse_date(li.get('endDate')),
#                         'ad_format': li.get('adFormat', []),
#                         'impressions': li.get('impressions') or None,
#                         'landing_page': li.get('landingPage') or None,
#                         'units': li.get('units') or None,
#                         'ctr': li.get('ctr') or None,
#                         'viewability': li.get('viewability') or None,
#                         'vcr': li.get('vcr') or None,
#                     }
#                 )

#                 creatives_meta = li.get('creatives', [])

#                 for j, meta in enumerate(creatives_meta):

#                     if not meta.get('creative_name'):
#                         continue

#                     main_asset = request.FILES.get(f'line_item_{i}_main_asset_{j}')
#                     backup_image = request.FILES.get(f'line_item_{i}_backup_image_{j}')

#                     Creative.objects.create(
#                         line_item=line_item,
#                         creative_name=meta.get('creative_name', ''),
#                         main_asset=main_asset,
#                         backup_image=backup_image,
#                         dimensions=meta.get('dimensions', ''),
#                         aspect_ratio=meta.get('aspect_ratio', ''),
#                         file_size=meta.get('file_size', ''),
#                         click_through_url=meta.get('click_through_url') or None,
#                         appended_html_tag=meta.get('appended_html_tag', ''),
#                         integration_code=meta.get('integration_code', ''),
#                         notes=meta.get('notes', ''),
#                         main_asset_name=main_asset.name if main_asset else '',
#                         backup_image_name=backup_image.name if backup_image else '',
#                     )

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

#     return Response({
#         "message": "Campaign created successfully",
#         "campaign_id": campaign.campaign_id,
#         "data": CampaignSerializer(campaign).data
#     }, status=status.HTTP_201_CREATED)





#===========================
# GET ALL CAMPAIGNS
# ==============================

from django.db.models import Prefetch

# @api_view(['GET'])
# def get_campaigns(request):

#     campaigns = Campaign.objects.select_related('client').prefetch_related(
#         Prefetch(
#             'line_items',
#             queryset=LineItem.objects.prefetch_related('line_items__creatives_detail')
#         )
#     )

#     serializer = CampaignSerializer(campaigns, many=True)
#     return Response(serializer.data)

@api_view(['GET'])
def get_campaigns(request):

    campaigns = Campaign.objects.select_related('client').prefetch_related(
        'line_items__creatives_detail'
    )

    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)

# @api_view(['GET'])
# def get_campaigns(request):

#     campaigns = Campaign.objects.select_related('client').prefetch_related(
#         Prefetch(
#             'line_items',
#             queryset=LineItem.objects.prefetch_related('creatives_detail')
#         )
#     )

#     serializer = CampaignSerializer(campaigns, many=True)
#     return Response(serializer.data)





# ==============================
# GET CAMPAIGNS BY CLIENT ID
# ==============================


# @api_view(['GET'])
# def get_campaigns_by_client(request, client_id):

#     try:
#         campaigns = Campaign.objects.filter(
#             client__client_id=client_id
#         ).select_related('client').prefetch_related(
#             Prefetch(
#                 'line_items',
#                 queryset=LineItem.objects.prefetch_related('creatives')
#             )
#         )

#         if not campaigns.exists():
#             return Response({"message": "No campaigns found for this client"}, status=404)

#         serializer = CampaignSerializer(campaigns, many=True)
#         return Response(serializer.data)

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def get_campaigns_by_client(request, client_id):

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
# @api_view(['GET'])
# def get_campaign_by_id(request, campaign_id):

#     try:
#         campaign = Campaign.objects.select_related('client').prefetch_related(
#             Prefetch(
#                 'line_items',
#                 queryset=LineItem.objects.prefetch_related('creatives')
#             )
#         ).get(campaign_id=campaign_id)

#     except Campaign.DoesNotExist:
#         return Response({"error": "Campaign not found"}, status=404)

#     serializer = CampaignSerializer(campaign)
#     return Response(serializer.data)

@api_view(['GET'])
def get_campaign_by_id(request, campaign_id):

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

# @api_view(['POST'])
# @parser_classes([MultiPartParser, FormParser])
# def upload_creatives(request):

#     line_item_id = request.data.get('line_item_id')

#     if not line_item_id:
#         return Response({"error": "line_item_id is required"}, status=400)

#     line_item, is_created = LineItem.objects.get_or_create(
#         line_item_id=line_item_id,
#         defaults={
#             'line_item_name': f'Pending - {line_item_id}',
#             'campaign': None,
#             'start_date': None,
#             'end_date': None,
#         }
#     )

#     try:
#         creatives_meta = json.loads(request.data.get('creatives_meta', '[]'))
#     except Exception:
#         return Response({"error": "Invalid creatives_meta JSON"}, status=400)

#     if not creatives_meta:
#         return Response({"error": "No creatives provided"}, status=400)

#     created_list = []
#     errors = []

#     try:
#         with transaction.atomic():

#             for i, meta in enumerate(creatives_meta):

#                 if not meta.get('creative_name'):
#                     errors.append({"index": i, "error": "creative_name is required"})
#                     continue

#                 main_asset = request.FILES.get(f'main_asset_{i}')
#                 backup_image = request.FILES.get(f'backup_image_{i}')

#                 # Optional validation
#                 if not main_asset and not backup_image:
#                     errors.append({"index": i, "error": "At least one file is required"})
#                     continue

#                 creative = Creative(
#                     line_item=line_item,
#                     creative_name=meta.get('creative_name', ''),
#                     main_asset=main_asset,
#                     backup_image=backup_image,
#                     dimensions=meta.get('dimensions', ''),
#                     aspect_ratio=meta.get('aspect_ratio', ''),
#                     file_size=meta.get('file_size', ''),
#                     click_through_url=meta.get('click_through_url') or None,
#                     appended_html_tag=meta.get('appended_html_tag', ''),
#                     integration_code=meta.get('integration_code', ''),
#                     notes=meta.get('notes', ''),
#                     main_asset_name=main_asset.name if main_asset else meta.get('main_asset_name') or '',
#                     backup_image_name=backup_image.name if backup_image else meta.get('backup_image_name') or '',
#                 )

#                 # Validate model
#                 creative.full_clean()
#                 creative.save()

#                 created_list.append(
#                     CreativeSerializer(creative, context={'request': request}).data
#                 )

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

#     return Response({
#         "message": f"{len(created_list)} creative(s) uploaded successfully",
#         "line_item_id": line_item_id,
#         "created_count": len(created_list),
#         "creatives": created_list,
#         "errors": errors,
#     }, status=status.HTTP_201_CREATED)




# ── GET creatives by line_item_id ──
@api_view(['GET'])
def get_creatives_by_line_item(request, line_item_id):
    try:
        line_item = LineItem.objects.get(id=line_item_id)
    except LineItem.DoesNotExist:
        return Response({"error": "LineItem not found"}, status=404)

    creatives = Creative.objects.filter(line_item=line_item)
    serializer = CreativeSerializer(creatives, many=True, context={'request': request})
    return Response(serializer.data) 


# --------------------------------------------


def parse_date(date_str):
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace('Z', '')).date()



@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_campaign(request):

    client_id = request.data.get('client')

    if not client_id:
        return Response({"error": "client is required"}, status=400)

    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        return Response({"error": f"Client '{client_id}' not found"}, status=404)

    serializer = CampaignSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    try:
        with transaction.atomic():

            campaign = serializer.save(client=client)

            # 🔥 IMPORTANT: JSON parse
            try:
                line_items_data = json.loads(request.data.get('line_items', '[]'))
            except Exception:
                return Response({"error": "Invalid line_items JSON"}, status=400)

            for i, li in enumerate(line_items_data):

                line_item_id = li.get('line_item_id')

                if not line_item_id:
                    continue

                # ✅ FIX: store object
                line_item, _ = LineItem.objects.update_or_create(
                    line_item_id=line_item_id,
                    defaults={
                        'campaign': campaign,
                        'line_item_name': li.get('lineItemName'),
                        'ethnicity': li.get('ethnicity', []),
                        'start_date': parse_date(li.get('startDate')),
                        'end_date': parse_date(li.get('endDate')),
                        'ad_format': li.get('adFormat', []),
                        'impressions': li.get('impressions') or None,
                        'landing_page': li.get('landingPage') or None,
                        'units': li.get('units') or None,
                        'ctr': li.get('ctr') or None,
                        'viewability': li.get('viewability') or None,
                        'vcr': li.get('vcr') or None,
                    }
                )

                # 🔥 creatives must come from frontend
                creatives_meta = li.get('creatives', [])

                for j, meta in enumerate(creatives_meta):

                    if not meta.get('creative_name'):
                        continue

                    # 🔥 VERY IMPORTANT (match frontend keys)
                    main_asset = request.FILES.get(f'line_item_{i}_main_asset_{j}')
                    backup_image = request.FILES.get(f'line_item_{i}_backup_image_{j}')

                    Creative.objects.create(
                        line_item=line_item,
                        creative_name=meta.get('creative_name', ''),
                        main_asset=main_asset,
                        backup_image=backup_image,
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