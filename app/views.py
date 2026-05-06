# ----- Import libraries ------

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Client, Campaign,LineItem, LineItemCreative, Creative
from .serializers import ClientSerializer, CampaignSerializer, CreativeSerializer
import json
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Prefetch

# Home
def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")


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

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])  # 🔥 IMPORTANT for files
def create_campaign(request):

    # -------------------------
    # 1. Validate client
    # -------------------------
    client_id = request.data.get('client')

    if not client_id:
        return Response({"error": "client is required"}, status=400)

    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        return Response({"error": f"Client '{client_id}' not found"}, status=404)

    # -------------------------
    # 2. Create Campaign
    # -------------------------
    data = request.data.copy()
    data.pop('client', None)

    serializer = CampaignSerializer(data=data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    campaign = serializer.save(client=client)

    # -------------------------
    # 3. Parse Line Items JSON
    # -------------------------
    try:
        line_items_data = json.loads(request.data.get('line_items', '[]'))
    except Exception:
        return Response({"error": "Invalid line_items JSON"}, status=400)

    # -------------------------
    # 4. Create Line Items
    # -------------------------
    # ── 4. Create / Update Line Items ──
    for i, li in enumerate(line_items_data):

        line_item, _ = LineItem.objects.update_or_create(
            line_item_id=li.get('line_item_id', ''),
            defaults={
                'campaign': campaign,
                'line_item_name': li.get('lineItemName'),
                'ethnicity': li.get('ethnicity', []),
                'start_date': li.get('startDate') or None,
                'end_date': li.get('endDate') or None,
                'ad_format': li.get('adFormat', []),
                'impressions': li.get('impressions') or None,
                'landing_page': li.get('landingPage') or None,
                'units': li.get('units') or None,
                'ctr': li.get('ctr') or None,
                'viewability': li.get('viewability') or None,
                'vcr': li.get('vcr') or None,
            }
        )

        # ── 5. Creatives (FILES) — unchanged ──
        for key, file in request.FILES.items():
            if key.startswith(f'line_item_{i}_creative'):
                LineItemCreative.objects.create(
                    line_item=line_item,
                    file=file
                )

    # -------------------------
    # 6. Response
    # -------------------------
    return Response({
        "message": "Campaign created successfully",
        "campaign_id": campaign.campaign_id,
        "data": CampaignSerializer(campaign).data
    }, status=status.HTTP_201_CREATED)




# ==============================
# GET ALL CAMPAIGNS
# ==============================

@api_view(['GET'])
def get_campaigns(request):

    campaigns = Campaign.objects.select_related('client').prefetch_related(
        Prefetch(
            'line_items',
            queryset=LineItem.objects.prefetch_related('creatives')
        )
    ).all()

    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)

# ==============================
# GET CAMPAIGNS BY CLIENT ID
# ==============================


@api_view(['GET'])
def get_campaigns_by_client(request, client_id):

    try:
        campaigns = Campaign.objects.filter(
            client__client_id=client_id
        ).select_related('client').prefetch_related(
            Prefetch(
                'line_items',
                queryset=LineItem.objects.prefetch_related('creatives')
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
def get_campaign_by_id(request, campaign_id):

    try:
        campaign = Campaign.objects.select_related('client').prefetch_related(
            Prefetch(
                'line_items',
                queryset=LineItem.objects.prefetch_related('creatives')
            )
        ).get(campaign_id=campaign_id)

    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    serializer = CampaignSerializer(campaign)
    return Response(serializer.data)



# -------------------------------------------------
# upload creatives 

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_creatives(request):

    line_item_id = request.data.get('line_item_id')

    if not line_item_id:
        return Response({"error": "line_item_id is required"}, status=400)

    line_item, is_created = LineItem.objects.get_or_create(
        line_item_id=line_item_id,
        defaults={
            'line_item_name': f'Pending - {line_item_id}',
            'campaign': None,
            'start_date': None,
            'end_date': None,
        }
    )

    try:
        creatives_meta = json.loads(request.data.get('creatives_meta', '[]'))
    except Exception:
        return Response({"error": "Invalid creatives_meta JSON"}, status=400)

    if not creatives_meta:
        return Response({"error": "No creatives provided"}, status=400)

    created_list = []
    errors = []

    for i, meta in enumerate(creatives_meta):
        try:
            if not meta.get('creative_name'):
                errors.append({"index": i, "error": "creative_name is required"})
                continue

            main_asset = request.FILES.get(f'main_asset_{i}')
            backup_image = request.FILES.get(f'backup_image_{i}')

            creative = Creative.objects.create(
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
                main_asset_name=main_asset.name if main_asset else meta.get('main_asset_name') or '',
                backup_image_name=backup_image.name if backup_image else meta.get('backup_image_name') or '',
            )

            created_list.append(
                CreativeSerializer(creative, context={'request': request}).data
            )

        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    return Response({
        "message": f"{len(created_list)} creative(s) uploaded successfully",
        "line_item_id": line_item_id,
        "created_count": len(created_list),
        "creatives": created_list,
        "errors": errors,
    }, status=status.HTTP_201_CREATED)







'''
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_creatives(request):

    # ── 1. Get line_item_id ──
    line_item_id = request.data.get('line_item_id')
    
    
    if not line_item_id:
        return Response({"error": "line_item_id is required"}, status=400)
    
    line_item, is_created = LineItem.objects.get_or_create(
        line_item_id=line_item_id,
        defaults={
            'line_item_name': f'Pending - {line_item_id}',
            'campaign': None,   # no campaign yet
            'start_date': None,
            'end_date': None,
        }

    )

    # try:
    #     line_item = LineItem.objects.get(line_item_id=line_item_id)
        
    # except LineItem.DoesNotExist:
    #     return Response({"error": f"LineItem '{line_item_id}' not found"}, status=404)

    # ── 2. Parse creatives_meta JSON ──
    try:
        creatives_meta = json.loads(request.data.get('creatives_meta', '[]'))
    except Exception:
        return Response({"error": "Invalid creatives_meta JSON"}, status=400)

    if not creatives_meta:
        return Response({"error": "No creatives provided"}, status=400)

    # ── 3. Create Creative objects ──
    created = []
    errors = []

    for i, meta in enumerate(creatives_meta):
        try:
            main_asset = request.FILES.get(f'main_asset_{i}')
            backup_image = request.FILES.get(f'backup_image_{i}')

            creative = Creative.objects.create(
                line_item=line_item,
                creative_name=meta.get('creative_name', ''),
                dimensions=meta.get('dimensions', ''),
                aspect_ratio=meta.get('aspect_ratio', ''),
                file_size=meta.get('file_size', ''),
                click_through_url=meta.get('click_through_url') or None,
                appended_html_tag=meta.get('appended_html_tag', ''),
                #integration_code=meta.get('ineg', ''),
                integration_code=meta.get('integration_code', ''),
                notes=meta.get('notes', ''),

                # File metadata
                main_asset_name=main_asset.name if main_asset else meta.get('main_asset_name', ''),
                backup_image_name=backup_image.name if backup_image else meta.get('backup_image_name', ''),
            )

            # Attach files separately (so model saves path correctly)
            if main_asset:
                creative.main_asset = main_asset
            if backup_image:
                creative.backup_image = backup_image

            creative.save()

            created.append(CreativeSerializer(creative, context={'request': request}).data)

        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    # ── 4. Response ──
    return Response({
        "message": f"{len(created)} creative(s) uploaded successfully",
        "line_item_id": line_item_id,
        "created_count": len(created),
        "creatives": created,
        "errors": errors,
    }, status=status.HTTP_201_CREATED)

'''



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