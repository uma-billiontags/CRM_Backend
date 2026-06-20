from django.http import FileResponse
from django.shortcuts import get_object_or_404
import mimetypes
from clients.models import Client
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from .models import Client, LineItem, Creative, ThirdPartyCreative, Campaign
from .serializers import CampaignSerializer
from .notification import send_push_notification
from django.http import HttpResponse
from datetime import datetime
import json
from django.db import transaction  # imports Django transaction management system.
from django.db.models import Prefetch
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from insertion_order.views import generate_io_for_campaign

# Create your views here.


# ==============================
# Home function
# ==============================
def home(request):
    return HttpResponse("Welcome to the CRM Home Page!")


# Creates a custom function to convert frontend date string into Python date.
def parse_date(date_str):

    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "")).date()


@api_view(["POST"])
@parser_classes(
    [MultiPartParser, FormParser]
)  # it allows file upload, formdata. (without this file uploads won't work)
def create_campaign(request):

    client_id = request.data.get(
        "client"
    )  # get the client id CLT-2026-00001 from frontend
    if not client_id:
        return Response(
            {"error": "client is required"}, status=400
        )  # if frontend not send throw this error

    # =====================================================
    # FIND CLIENT
    # =====================================================

    try:
        client = Client.objects.get(
            client_id=client_id
        )  # find the client(full details) from database
    except Client.DoesNotExist:
        return Response({"error": f"Client '{client_id}' not found"}, status=404)

    # =====================================================
    # VALIDATE CAMPAIGN
    # =====================================================

    serializer = CampaignSerializer(
        data=request.data
    )  # Take all data coming from frontend request and give it to serializer.
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    try:
        with transaction.atomic():  # save together
            campaign = serializer.save(client=client)  # save campagin

            try:
                line_items_data = json.loads(
                    request.data.get("line_items", "[]")
                )  # get the line items from frontend and converts json into python dict
            except Exception:
                return Response({"error": "Invalid line_items JSON"}, status=400)

            # =============================================
            # LOOP LINE ITEMS
            # =============================================

            for i, li in enumerate(
                line_items_data
            ):  # Loop through every line item one by one. (eg: i=0, li=first line item)

                line_item_id = li.get(
                    "line_item_id"
                )  # get the line item id (LIUSER0001)

                if not line_item_id:  # If no ID, skip that line item.
                    continue

                line_item, _ = (
                    LineItem.objects.update_or_create(  # Search LineItem using line_item_id (if line item data already exist (update) or (create))
                        line_item_id=line_item_id,
                        defaults={
                            "campaign": campaign,
                            "line_item_name": li.get("lineItemName"),
                            "ethnicity": li.get("ethnicity", []),
                            "start_date": parse_date(li.get("startDate")),
                            "end_date": parse_date(li.get("endDate")),
                            "ad_format": li.get("adFormat", []),
                            "impressions": li.get("impressions") or None,
                            "units": li.get("units") or None,
                            "ctr": li.get("ctr") or None,
                            "viewability": li.get("viewability") or None,
                            "vcr": li.get("vcr") or None,
                            "unit_cost": li.get("unit_cost") or None,
                            "kpi_notes": li.get("kpi_notes", ""),
                            "unit_value": li.get("unit_value") or None,
                            "age": li.get("age", ""),
                            "gender": li.get("gender", ""),
                            "geo_targeting": li.get("geo_targeting", ""),
                            "platforms": li.get("platforms", ""),
                            "frequency_cap": li.get("frequency_cap") or None,
                            "brand_safety": li.get("brand_safety", ""),
                        },
                    )
                )

                # Fix — two separate loops

                # Loop 1: normal creatives
                creatives_meta = li.get("creatives", [])
                for j, meta in enumerate(creatives_meta):
                    if not meta.get("creative_name"):
                        continue

                    main_asset = request.FILES.get(f"line_item_{i}main_asset{j}")
                    Creative.objects.create(
                        line_item=line_item,
                        creative_name=meta.get("creative_name", ""),
                        main_asset=main_asset,
                        dimensions=meta.get("dimensions", ""),
                        aspect_ratio=meta.get("aspect_ratio", ""),
                        file_size=meta.get("file_size", ""),
                        click_through_url=meta.get("click_through_url") or None,
                        appended_html_tag=meta.get("appended_html_tag", ""),
                        integration_code=meta.get("integration_code", ""),
                        notes=meta.get("notes", ""),
                    )

                # Loop 2: third-party creatives — completely separate
                third_party_meta = li.get("third_party_creatives", [])
                for k, _ in enumerate(third_party_meta):
                    input_file = request.FILES.get(f"line_item_{i}thirdparty_file{k}")
                    backup_image = request.FILES.get(
                        f"line_item_{i}thirdparty_backup{k}"
                    )
                    ThirdPartyCreative.objects.create(
                        line_item=line_item,
                        input_file=input_file,
                        backup_image=backup_image,
                    )

    except Exception as e:
        return Response({"error": str(e)}, status=500)

    # =============================================
    # SEND FIREBASE PUSH NOTIFICATION
    # =============================================

    send_push_notification(
        "New Campaign Submitted",
        # f"Campaign {campaign.campaign_id} submitted for client {client.name}"
        f"{client.name} submitted the campaign for client ID {client.client_id}",
    )

    return Response(
        {
            "message": (
                "Campaign + LineItem + "
                "Creative + ThirdPartyCreative "
                "saved successfully"
            ),
            "campaign_id": campaign.campaign_id,
        },
        status=201,
    )


# ===========================
# GET ALL CAMPAIGNS
# ==========================


@api_view(["GET"])
def get_campaigns(request):

    campaigns = Campaign.objects.select_related("client").prefetch_related(
        "line_items__creatives_detail", "line_items__third_party_creatives"
    )
    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)


# ==============================
# GET CAMPAIGNS BY CLIENT ID
# ==============================


@api_view(["GET"])
def get_campaigns_by_client(
    request, client_id
):  # http://127.0.0.1:8000/get_campaigns_by_client/CLT-2026-00001/

    try:
        campaigns = (
            Campaign.objects.filter(client__client_id=client_id)
            .select_related("client")
            .prefetch_related(
                Prefetch(
                    "line_items",
                    queryset=LineItem.objects.prefetch_related("creatives_detail"),
                )
            )
        )

        if not campaigns.exists():
            return Response(
                {"message": "No campaigns found for this client"}, status=404
            )

        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ==============================
# GET CAMPAIGNS BY CAMPAIGN ID
# ==============================


@api_view(["GET"])
def get_campaign_by_id(
    request, campaign_id
):  # http://127.0.0.1:8000/get_campaign_by_id/CMP-2026-00001/

    try:
        campaign = (
            Campaign.objects.select_related("client")
            .prefetch_related(
                Prefetch(
                    "line_items",
                    queryset=LineItem.objects.prefetch_related("creatives_detail"),
                )
            )
            .get(campaign_id=campaign_id)
        )

    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    serializer = CampaignSerializer(campaign)
    return Response(serializer.data)


# =========================================================
# UPDATE CAMPAIGN
# =========================================================


@api_view(["GET", "PUT"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_campaign(request, campaign_id):

    # =====================================================
    # FIND CAMPAIGN
    # =====================================================

    try:

        campaign = (
            Campaign.objects.select_related("client")
            .prefetch_related(
                "line_items__creatives_detail", "line_items__third_party_creatives"
            )
            .get(campaign_id=campaign_id)
        )

    except Campaign.DoesNotExist:

        return Response({"error": "Campaign not found"}, status=404)

    # =====================================================
    # GET CAMPAIGN
    # =====================================================

    if request.method == "GET":

        serializer = CampaignSerializer(campaign, context={"request": request})

        return Response(serializer.data)

    # =====================================================
    # UPDATE CAMPAIGN
    # =====================================================

    try:

        with transaction.atomic():

            data = {}
            for key, value in request.data.items():
                if key != "line_items":  # ← exclude line_items from campaign serializer
                    data[key] = value

            serializer = CampaignSerializer(
                campaign, data=request.data, partial=True, context={"request": request}
            )

            if not serializer.is_valid():

                return Response(serializer.errors, status=400)

            # =============================================
            # SAVE CAMPAIGN
            # =============================================

            serializer.save(
                new_cpm=(
                    request.data.get("new_cpm") if request.data.get("new_cpm") else None
                ),
                new_price=(
                    request.data.get("new_price")
                    if request.data.get("new_price")
                    else None
                ),
            )

            # =============================================
            # GET LINE ITEMS
            # =============================================

            try:

                line_items_data = json.loads(request.data.get("line_items", "[]"))

            except Exception:

                return Response({"error": "Invalid line_items JSON"}, status=400)

            # =============================================
            # LOOP LINE ITEMS
            # =============================================

            for i, li in enumerate(line_items_data):

                line_item_id = li.get("line_item_id")

                if not line_item_id:
                    continue

                line_item, _ = LineItem.objects.update_or_create(
                    line_item_id=line_item_id,
                    defaults={
                        "campaign": campaign,
                        "line_item_name": li.get("lineItemName"),
                        "ethnicity": li.get("ethnicity", []),
                        "start_date": parse_date(li.get("startDate")),
                        "end_date": parse_date(li.get("endDate")),
                        "ad_format": li.get("adFormat", []),
                        "impressions": li.get("impressions") or None,
                        "units": li.get("units") or None,
                        "ctr": li.get("ctr") or None,
                        "viewability": li.get("viewability") or None,
                        "vcr": li.get("vcr") or None,
                        "unit_cost": li.get("unit_cost") or None,
                        "kpi_notes": li.get("kpi_notes", ""),
                        "unit_value": li.get("unit_value") or None,
                        "age": li.get("age", ""),
                        "gender": li.get("gender", ""),
                        "geo_targeting": li.get("geo_targeting", ""),
                        "platforms": li.get("platforms", ""),
                        "frequency_cap": li.get("frequency_cap") or None,
                        "brand_safety": li.get("brand_safety", ""),
                    },
                )

                # =============================================
                # NORMAL CREATIVES
                # =============================================

                creatives_meta = li.get("creatives", [])

                for j, meta in enumerate(creatives_meta):

                    if not meta.get("creative_name"):
                        continue

                    main_asset = request.FILES.get(f"line_item_{i}main_asset{j}")

                    Creative.objects.create(
                        line_item=line_item,
                        creative_name=meta.get("creative_name", ""),
                        main_asset=main_asset,
                        dimensions=meta.get("dimensions", ""),
                        aspect_ratio=meta.get("aspect_ratio", ""),
                        file_size=meta.get("file_size", ""),
                        click_through_url=meta.get("click_through_url") or None,
                        appended_html_tag=meta.get("appended_html_tag", ""),
                        integration_code=meta.get("integration_code", ""),
                        notes=meta.get("notes", ""),
                    )

                # =============================================
                # THIRD PARTY CREATIVES
                # =============================================

                third_party_meta = li.get("third_party_creatives", [])

                for k, _ in enumerate(third_party_meta):

                    input_file = request.FILES.get(f"line_item_{i}thirdparty_file{k}")

                    backup_image = request.FILES.get(
                        f"line_item_{i}thirdparty_backup{k}"
                    )

                    ThirdPartyCreative.objects.create(
                        line_item=line_item,
                        input_file=input_file,
                        backup_image=backup_image,
                    )

    except Exception as e:

        import traceback

        print(traceback.format_exc())

        return Response({"error": str(e)}, status=500)

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================

    return Response(
        {
            "message": "Campaign updated successfully",
            "campaign_id": campaign.campaign_id,
        },
        status=200,
    )


# =========================================================
# DELETE CAMPAIGN
# =========================================================


@api_view(["DELETE"])
def delete_campaign(request, campaign_id):

    # =====================================================
    # FIND CAMPAIGN
    # =====================================================

    try:

        # ✅ Try campaign_id string first, fallback to pk
        try:
            campaign = Campaign.objects.get(campaign_id=campaign_id)
        except Campaign.DoesNotExist:
            # For pending campaigns where campaign_id is null, try pk
            campaign = Campaign.objects.get(pk=campaign_id)

    except Campaign.DoesNotExist:

        return Response({"error": "Campaign not found"}, status=404)

    # =====================================================
    # DELETE CAMPAIGN
    # =====================================================

    campaign.delete()

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================

    return Response(
        {"message": "Campaign deleted successfully", "campaign_id": campaign_id},
        status=200,
    )


from .notification import send_notification_to_client


@api_view(["POST"])
def approve_campaign(request, pk):
    try:
        campaign = Campaign.objects.get(pk=pk)
    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    # ✅ Check approval_status instead of campaign_id
    if campaign.approval_status == "approved":
        return Response({"error": "Campaign already approved"}, status=400)

    # if campaign.campaign_id:
    #     return Response({"error": "Campaign already approved"}, status=400)

    try:
        with transaction.atomic():
            new_id = campaign.generate_campaign_id()

            # Extra safety: ensure uniqueness
            counter = 1
            original_id = new_id
            while Campaign.objects.filter(campaign_id=new_id).exists():
                # Increment last number manually
                parts = new_id.split("-")
                num = int(parts[-1]) + counter
                new_id = f"{'-'.join(parts[:-1])}-{str(num).zfill(5)}"
                counter += 1

            # Assign and save
            campaign.campaign_id = new_id
            campaign.approval_status = "approved"
            campaign.save()  # This is critical

            # IO generation
            io_id = generate_io_for_campaign(new_id)

            # Send notification
            send_notification_to_client(
                campaign.client,
                "Campaign Approved",
                f"Your campaign {campaign.campaign_name} has been approved with ID: {new_id}",
            )

            print(f"✅ Campaign approved successfully: {new_id}")  # For debugging

            return Response(
                {
                    "message": "Campaign approved successfully",
                    "campaign_id": campaign.campaign_id,
                    "io_id": io_id,
                },
                status=200,
            )

    except Exception as e:
        import traceback

        print("❌ Approve Campaign Error:")
        print(traceback.format_exc())
        return Response(
            {"error": str(e), "details": "Check server logs for full traceback"},
            status=500,
        )


@api_view(["GET"])
def download_creative(request, creative_id):

    # Get creative object
    creative = get_object_or_404(Creative, id=creative_id)

    # Get uploaded file path
    file_path = creative.main_asset.path

    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    # Return downloadable response
    return FileResponse(
        open(file_path, "rb"), as_attachment=True, content_type=mime_type
    )


# Third party function
@api_view(["GET"])
def download_thirdparty(request, thirdparty_id):

    # Get third-party creative object
    thirdparty = get_object_or_404(ThirdPartyCreative, id=thirdparty_id)

    if not thirdparty.input_file:
        return Response({"error": "No input file uploaded"}, status=404)

    # Get uploaded file path
    file_path = thirdparty.input_file.path

    # Return downloadable response
    return FileResponse(
        open(file_path, "rb"), as_attachment=True, filename=thirdparty.input_file.name
    )


# Backup image function
@api_view(["GET"])
def download_backup_image(request, thirdparty_id):

    thirdparty = get_object_or_404(ThirdPartyCreative, id=thirdparty_id)

    if not thirdparty.backup_image:
        return Response({"error": "No input file uploaded"}, status=404)
    file_path = thirdparty.backup_image.path
    return FileResponse(
        open(file_path, "rb"), as_attachment=True, filename=thirdparty.backup_image.name
    )


@api_view(["PATCH"])
def update_creative_id(request):
    creative_type = request.data.get("type")  # 'standard' or 'third_party'
    creative_db_id = request.data.get("id")  # DB primary key (integer)
    creative_id_value = request.data.get("creative_id", "").strip()

    if not creative_db_id or not creative_type:
        return Response({"error": "id and type are required"}, status=400)

    try:
        if creative_type == "standard":
            obj = Creative.objects.get(id=creative_db_id)
            obj.creative_id = creative_id_value
            obj.save()
            return Response(
                {
                    "message": "Creative ID Added Successfully",
                    "id": obj.id,
                    "creative_id": obj.creative_id,
                },
                status=200,
            )

        elif creative_type == "third_party":
            obj = ThirdPartyCreative.objects.get(id=creative_db_id)
            obj.creative_id = creative_id_value
            obj.save()
            return Response(
                {
                    "message": "Creative ID Added Successfully",
                    "id": obj.id,
                    "creative_id": obj.creative_id,
                },
                status=200,
            )

        else:
            return Response(
                {"error": "Invalid type. Use 'standard' or 'third_party'"}, status=400
            )

    except (Creative.DoesNotExist, ThirdPartyCreative.DoesNotExist):
        return Response({"error": "Creative not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["PATCH"])
def update_line_item_dv_id(request, line_item_id):
    """
    PATCH /update_line_item_dv_id/<line_item_id>/
    Body: { "dv_id": "DV360_12345" }
    """
    try:
        line_item = LineItem.objects.get(line_item_id=line_item_id)
    except LineItem.DoesNotExist:
        return Response({"error": "LineItem not found"}, status=404)

    dv_id = request.data.get("dv_id", "").strip()
    line_item.dv_id = dv_id
    line_item.save(update_fields=["dv_id"])

    return Response({
        "message": "DV ID updated successfully",
        "line_item_id": line_item_id,
        "dv_id": line_item.dv_id,
    }, status=200)
    

from .models import BulkCampaignDetails, BulkCampaignAttachment


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def create_bulk_campaign(request):

    client_id = request.data.get("client")
    client_name = request.data.get("client_name", "")

    # Client lookup is best-effort — still save the request even if not found
    client = None
    if client_id:
        try:
            client = Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            client = None

    advertiser = request.data.get("advertiser")
    campaign_name = request.data.get("campaign_name")
    campaign_type = request.data.get("campaign_type")
    objective = request.data.get("objective")

    if not advertiser or not campaign_name or not campaign_type or not objective:
        return Response(
            {"error": "advertiser, campaign_name, campaign_type and objective are required"},
            status=400,
        )

    try:
        with transaction.atomic():
            bulk_campaign = BulkCampaignDetails.objects.create(
                client=client,
                client_name=client_name,
                advertiser=advertiser,
                website_url=request.data.get("website_url") or None,
                client_campaign_id=request.data.get("client_campaign_id") or None,
                purchase_order_id=request.data.get("purchase_order_id") or None,
                campaign_name=campaign_name,
                campaign_type=campaign_type,
                buying_type=request.data.get("buying_type", ""),
                objective=objective,
                start_date=parse_date(request.data.get("start_date")),
                end_date=parse_date(request.data.get("end_date")),
                message=request.data.get("message", ""),
            )

            attachment_count = int(request.data.get("attachment_count") or 0)
            for i in range(attachment_count):
                file_obj = request.FILES.get(f"attachment_{i}")
                if not file_obj:
                    continue
                BulkCampaignAttachment.objects.create(
                    bulk_campaign=bulk_campaign,
                    file=file_obj,
                    file_name=file_obj.name,
                    file_type=file_obj.content_type or "",
                )

    except Exception as e:
        return Response({"error": str(e)}, status=500)

    return Response(
        {
            "message": "Bulk campaign request submitted successfully",
            "id": bulk_campaign.id,
        },
        status=201,
    )
    

from .serializers import BulkCampaignDetailsSerializer

@api_view(["GET"])
def get_bulk_campaigns(request):
    bulk_campaigns = BulkCampaignDetails.objects.select_related("client").prefetch_related("attachments")
    serializer = BulkCampaignDetailsSerializer(bulk_campaigns, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["PATCH"])
def update_bulk_campaign_status(request, pk):
    try:
        bulk_campaign = BulkCampaignDetails.objects.get(pk=pk)
    except BulkCampaignDetails.DoesNotExist:
        return Response({"error": "Bulk campaign request not found"}, status=404)

    status_val = request.data.get("status")
    if status_val not in ("pending", "processed"):
        return Response({"error": "status must be 'pending' or 'processed'"}, status=400)

    bulk_campaign.status = status_val
    bulk_campaign.save(update_fields=["status"])
    return Response({"message": "Status updated", "id": bulk_campaign.id, "status": bulk_campaign.status})