from django.shortcuts import render
from rest_framework.response import Response
import io
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.http import FileResponse, HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Campaign, CampaignExcel
from django.core.files.base import ContentFile
from datetime import datetime
from campaigns.models import LineItem

# Create your views here.


def parse_date(date_str):

    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "")).date()


def build_campaign_excel(campaign, report_type="cpm", overrides=None) -> bytes:
    """
    overrides = { "LIBILL003": { "impressions": 50000, "start_date": "2026-06-01", ... } }
    """
    overrides = overrides or {}
    wb = Workbook()
    wb.remove(wb.active)

    # ── Styles (same as before) ──
    header_font = Font(name="Arial", bold=True, size=10)
    value_font = Font(name="Arial", size=10)
    label_fill = PatternFill("solid", start_color="D9E1F2")
    title_fill = PatternFill("solid", start_color="1F4E79")
    title_font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    border_side = Side(style="thin", color="B8CCE4")
    thin_border = Border(
        left=border_side, right=border_side, top=border_side, bottom=border_side
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

    line_items = campaign.line_items.all()

    for li in line_items:
        sheet_name = str(li.line_item_id)[:31]
        ws = wb.create_sheet(title=sheet_name)
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 40

        ws.merge_cells("A1:B1")
        ws["A1"] = f"Campaign Report — {campaign.campaign_id}"
        ws["A1"].font = title_font
        ws["A1"].fill = title_fill
        ws["A1"].alignment = center_align
        ws.row_dimensions[1].height = 22

        insertion_order = getattr(campaign, "insertion_order", None)
        is_cpc = report_type == "cpc"
        has_creatives = (
            li.creatives_detail.exists() or li.third_party_creatives.exists()
        )
        creative_msg = (
            "Creatives will be shared by Creatives Team"
            if has_creatives
            else "Not yet received"
        )

        # ✅ Get overrides for this line item
        li_overrides = overrides.get(li.line_item_id, {})

        # ✅ Use override value if present, else use DB value
        def val(field, db_value):
            return li_overrides.get(field, db_value)

        impressions = val("impressions", li.impressions)
        start_date = val("start_date", str(li.start_date) if li.start_date else "")
        end_date = val("end_date", str(li.end_date) if li.end_date else "")
        units = val("units", li.units or "")
        ctr_raw = val("ctr", li.ctr)
        viewability_raw = val("viewability", li.viewability)
        vcr_raw = val("vcr", li.vcr)
        kpi_notes = val("kpi_notes", li.kpi_notes or "")
        sitelist = val("sitelist", "")

        ctr_display = f"{ctr_raw}%" if ctr_raw else ""
        viewability_display = f"{viewability_raw}%" if viewability_raw else ""
        vcr_display = f"{vcr_raw}%" if vcr_raw else ""

        if is_cpc:
            rows = [
                (
                    "Date of ID Setup",
                    (
                        campaign.created_at.strftime("%d-%B-%Y")
                        if campaign.created_at
                        else ""
                    ),
                ),
                ("Advertiser ID", campaign.client_campaign_ID or ""),
                ("Campaign ID", f"{campaign.campaign_id}-A"),
                ("IO ID", insertion_order.io_id if insertion_order else ""),
                ("IO Name", campaign.campaign_name or ""),
                ("Clicks Booked", impressions or ""),
                ("Start Date", start_date),
                ("End Date", end_date),
                ("Target CPC", ctr_display),
                ("Booked Budget", ""),  # ← CPC: Booked Budget row, empty value
                ("Line Item ID", li.line_item_id or ""),
                ("Line Item Name", li.line_item_name or ""),
                ("Ethnicity", li.ethnicity or ""),
                ("Ad Format", li.ad_format or ""),
                ("Geography", _parse_geo(li.geo_targeting) if li.geo_targeting else ""),
                ("Market", ""),
                ("Viewability", viewability_display),
                ("Creative", creative_msg),
                ("VCR", vcr_display),
                ("Daily Clicks", ""),  # ← CPC only row
                ("Sitelist", sitelist),
            ]
        else:
            rows = [
                (
                    "Date of ID Setup",
                    (
                        campaign.created_at.strftime("%d-%B-%Y")
                        if campaign.created_at
                        else ""
                    ),
                ),
                ("Advertiser ID", campaign.client_campaign_ID or ""),
                ("Campaign ID", campaign.campaign_id),
                ("IO ID", insertion_order.io_id if insertion_order else ""),
                ("IO Name", campaign.campaign_name or ""),
                ("Impressions Booked", impressions or ""),
                ("Start Date", start_date),
                ("End Date", end_date),
                ("Target CPM", ctr_display),
                ("Target CTR", ctr_display),  # ← CPM: Target CTR row
                ("Line Item ID", li.line_item_id or ""),
                ("Line Item Name", li.line_item_name or ""),
                ("Ethnicity", li.ethnicity or ""),
                ("Ad Format", li.ad_format or ""),
                ("Geography", _parse_geo(li.geo_targeting) if li.geo_targeting else ""),
                ("Market", ""),
                ("Viewability", viewability_display),
                ("Creative", creative_msg),
                ("VCR", vcr_display),
                ("KPI", kpi_notes),
                ("Sitelist", sitelist),
            ]
        for i, (label, value) in enumerate(rows, start=2):
            label_cell = ws.cell(row=i, column=1, value=label)
            value_cell = ws.cell(row=i, column=2, value=value)
            label_cell.font = header_font
            label_cell.fill = label_fill
            label_cell.alignment = left_align
            label_cell.border = thin_border
            value_cell.font = value_font
            value_cell.alignment = left_align
            value_cell.border = thin_border
            ws.row_dimensions[i].height = 18

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


def _parse_geo(geo_targeting):
    """Parse geo_targeting field (JSON string or list) into readable string."""
    try:
        if isinstance(geo_targeting, str):
            data = json.loads(geo_targeting)
        else:
            data = geo_targeting
        parts = []
        for loc in (data if isinstance(data, list) else [data]):
            segment = ", ".join(
                filter(
                    None,
                    [loc.get("country", ""), loc.get("state", ""), loc.get("city", "")],
                )
            )
            if segment:
                parts.append(segment)
        return " | ".join(parts) if parts else ""
    except Exception:
        return str(geo_targeting) if geo_targeting else ""


# ── Generate & store Excel ──────────────────────────────────────────────────


@api_view(["POST"])
def generate_campaign_excel(request, campaign_id):
    try:
        campaign = (
            Campaign.objects.select_related("client", "insertion_order")
            .prefetch_related(
                "line_items",
                "line_items__creatives_detail",
                "line_items__third_party_creatives",
            )
            .get(campaign_id=campaign_id)
        )
    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    report_type = request.data.get("report_type", "cpm")

    # ── Get existing overrides if record exists ──
    existing_overrides = {}
    try:
        existing_excel = CampaignExcel.objects.get(
            campaign=campaign, report_type=report_type
        )
        existing_overrides = existing_excel.line_item_overrides or {}
    except CampaignExcel.DoesNotExist:
        pass

    # ── Always regenerate with existing overrides ──
    excel_bytes = build_campaign_excel(
        campaign, report_type, overrides=existing_overrides
    )
    filename = f"{campaign_id}_{report_type}.xlsx"

    # ── get_or_create then always save the file ──
    excel_obj, _ = CampaignExcel.objects.get_or_create(
        campaign=campaign, report_type=report_type, defaults={"line_item_overrides": {}}
    )
    excel_obj.excel_file.save(filename, ContentFile(excel_bytes), save=True)

    url = request.build_absolute_uri(excel_obj.excel_file.url)
    return Response(
        {
            "message": "Excel generated successfully",
            "campaign_id": campaign_id,
            "download_url": url,
            "filename": filename,
            "generated_at": excel_obj.generated_at.isoformat(),
        },
        status=200,
    )


@api_view(["GET"])
def get_campaigns_excel_list(request):
    campaigns = (
        Campaign.objects.select_related("client")
        .filter(approval_status="approved")
        .prefetch_related("excel_reports", "line_items")
        .order_by("-created_at")
    )

    data = []
    for c in campaigns:
        excel_map = {e.report_type: e for e in c.excel_reports.all()}

        # ✅ Check units across all line items
        all_units = [(li.units or "").upper() for li in c.line_items.all() if li.units]

        has_cpm = any(u == "CPM" for u in all_units)
        has_cpc = any(u == "CPC" for u in all_units)

        # ✅ Decide which report types to generate
        if has_cpm and has_cpc:
            report_types = ["cpm", "cpc"]  # both units → both reports
        elif has_cpc:
            report_types = ["cpc"]  # only CPC → one report (no -A suffix)
        else:
            report_types = ["cpm", "cpc"]  # only CPM or unknown → both reports

        for report_type in report_types:
            excel = excel_map.get(report_type)
            suffix = "-A" if report_type == "cpc" else ""
            data.append(
                {
                    "campaign_id": f"{c.campaign_id}{suffix}",
                    "campaign_id_raw": c.campaign_id,
                    "report_type": report_type,
                    "campaign_name": c.campaign_name,
                    "client_name": c.client.name if c.client else "",
                    "client_id": c.client.client_id if c.client else "",
                    "start_date": str(c.start_date) if c.start_date else "",
                    "end_date": str(c.end_date) if c.end_date else "",
                    "line_items_count": c.line_items.count(),
                    "excel_generated": excel is not None,
                    "excel_url": (
                        request.build_absolute_uri(excel.excel_file.url)
                        if excel
                        else None
                    ),
                    "generated_at": excel.generated_at.isoformat() if excel else None,
                    "publish_status": excel.publish_status if excel else None,
                }
            )

    return Response(data)


# ── Download saved Excel ────────────────────────────────────────────────────


@api_view(["GET"])
def download_campaign_excel(request, campaign_id):
    # ✅ Read report_type from query param
    report_type = request.query_params.get("report_type", "cpm")

    try:
        excel_obj = CampaignExcel.objects.get(
            campaign__campaign_id=campaign_id,
            report_type=report_type,  # ✅ Add this filter
        )
    except CampaignExcel.DoesNotExist:
        # Generate on-the-fly if not saved yet
        try:
            campaign = (
                Campaign.objects.select_related("client", "insertion_order")
                .prefetch_related("line_items")
                .get(campaign_id=campaign_id)
            )
        except Campaign.DoesNotExist:
            return Response({"error": "Campaign not found"}, status=404)

        excel_bytes = build_campaign_excel(campaign, report_type)
        response = HttpResponse(
            excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{campaign_id}_{report_type}.xlsx"'
        )
        return response

    response = FileResponse(
        excel_obj.excel_file.open("rb"),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{campaign_id}_{report_type}.xlsx"'
    )
    return response


@api_view(["POST"])
def save_excel_edits_to_db(request, campaign_id):
    try:
        report_type = request.data.get("report_type", "cpm")
        line_item_id = request.data.get("line_item_id")

        if not line_item_id:
            return Response(
                {"error": "line_item_id is required"},
                status=400,
            )

        # ── 1. Get CampaignExcel record ──
        try:
            excel_obj = CampaignExcel.objects.get(
                campaign__campaign_id=campaign_id,
                report_type=report_type,
            )
        except CampaignExcel.DoesNotExist:
            return Response(
                {"error": "Excel record not found. Generate first."},
                status=404,
            )

        # ── 2. Get LineItem (read-only, never modified) ──
        try:
            line_item = LineItem.objects.get(line_item_id=line_item_id)
        except LineItem.DoesNotExist:
            return Response(
                {"error": "LineItem not found"},
                status=404,
            )

        # ── 3. Get Campaign ──
        try:
            campaign = (
                Campaign.objects.select_related(
                    "client",
                    "insertion_order",
                )
                .prefetch_related(
                    "line_items",
                    "line_items__creatives_detail",
                    "line_items__third_party_creatives",
                )
                .get(campaign_id=campaign_id)
            )
        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found"},
                status=404,
            )

        editable_fields = [
            "impressions",
            "start_date",
            "end_date",
            "units",
            "ctr",
            "viewability",
            "vcr",
            "kpi_notes",
            "sitelist",
            "advertiser_id",
            "target_cpm",
            "target_ctr",
            "target_cpc",
            "booked_budget",
        ]

        # ── 4. Build override dict ──
        li_override = excel_obj.line_item_overrides.get(
            line_item_id,
            {},
        )

        for field in editable_fields:
            if field in request.data and request.data[field] is not None:
                li_override[field] = request.data[field]

        # ── 5. Save overrides to CampaignExcel.line_item_overrides ──
        overrides = excel_obj.line_item_overrides.copy()
        overrides[line_item_id] = li_override

        excel_obj.line_item_overrides = overrides
        excel_obj.save(update_fields=["line_item_overrides"])

        # ── 6. Save ONLY to CampaignLineItemExcelDetails ──
        from .models import CampaignLineItemExcelDetails

        def safe_int(value):
            try:
                return int(str(value).replace(",", "").strip())
            except Exception:
                return None

        def safe_float(value):
            try:
                return float(str(value).replace("%", "").strip())
            except Exception:
                return None

        excel_li_obj, _ = CampaignLineItemExcelDetails.objects.update_or_create(
            line_item=line_item,
            report_type=report_type,
            defaults={
                "campaign": campaign,
                # CPM report → impressions
                "impressions": (
                    safe_int(li_override["impressions"])
                    if report_type == "cpm" and "impressions" in li_override
                    else None
                ),
                # CPC report → clicks
                "clicks": (
                    safe_int(li_override["impressions"])
                    if report_type == "cpc" and "impressions" in li_override
                    else None
                ),
                "start_date": (
                    parse_date(str(li_override["start_date"]))
                    if li_override.get("start_date")
                    else None
                ),
                "end_date": (
                    parse_date(str(li_override["end_date"]))
                    if li_override.get("end_date")
                    else None
                ),
                "advertiser_id": (
                    li_override.get("advertiser_id")
                    or campaign.client_campaign_ID
                    or ""
                ),
                "target_cpm": (
                    safe_float(li_override["target_cpm"])
                    if "target_cpm" in li_override
                    else None
                ),
                "target_ctr": (
                    safe_float(li_override["target_ctr"])
                    if "target_ctr" in li_override
                    else None
                ),
                "target_cpc": (
                    safe_float(li_override["target_cpc"])
                    if report_type == "cpc" and "target_cpc" in li_override
                    else None
                ),
                "booked_budget": (
                    safe_float(li_override["booked_budget"])
                    if report_type == "cpc" and "booked_budget" in li_override
                    else None
                ),
                "sitelist": li_override.get(
                    "sitelist",
                    "",
                ),
            },
        )

        # ── 7. Re-generate Excel with updated overrides ──
        excel_bytes = build_campaign_excel(
            campaign,
            report_type,
            overrides=overrides,
        )

        filename = f"{campaign_id}_{report_type}.xlsx"

        excel_obj.excel_file.save(
            filename,
            ContentFile(excel_bytes),
            save=True,
        )

        url = request.build_absolute_uri(excel_obj.excel_file.url)

        return Response(
            {
                "message": "Saved to CampaignLineItemExcelDetails only (LineItem unchanged)",
                "download_url": url,
                "line_item_overrides": overrides,
                "excel_line_item_id": excel_li_obj.id,
            },
            status=200,
        )

    except Exception as e:
        import traceback

        print(traceback.format_exc())

        return Response(
            {"error": str(e)},
            status=500,
        )


@api_view(["GET"])
def get_line_item_excel_data(request, campaign_id):
    from .models import CampaignLineItemExcelDetails

    report_type = request.query_params.get("report_type", "cpm")

    try:
        campaign = (
            Campaign.objects.select_related("client")
            .prefetch_related("line_items")
            .get(campaign_id=campaign_id)
        )
    except Campaign.DoesNotExist:
        return Response({"error": "Campaign not found"}, status=404)

    data = {}
    for li in campaign.line_items.all():
        try:
            # ── Already saved → return saved values ──
            excel_data = CampaignLineItemExcelDetails.objects.get(
                line_item=li, report_type=report_type
            )
            data[li.line_item_id] = {
                "impressions": excel_data.impressions,
                "clicks": excel_data.clicks,
                "start_date": (
                    str(excel_data.start_date) if excel_data.start_date else ""
                ),
                "end_date": str(excel_data.end_date) if excel_data.end_date else "",
                "advertiser_id": excel_data.advertiser_id
                or campaign.client_campaign_ID
                or "",
                "target_cpm": excel_data.target_cpm,
                "target_ctr": excel_data.target_ctr,
                "target_cpc": excel_data.target_cpc,
                "booked_budget": excel_data.booked_budget,
                "sitelist": excel_data.sitelist or "",
            }
        except CampaignLineItemExcelDetails.DoesNotExist:
            # ── Not saved yet → return defaults from Campaign + LineItem ──
            data[li.line_item_id] = {
                "impressions": li.impressions,
                "clicks": None,
                "start_date": str(li.start_date) if li.start_date else "",
                "end_date": str(li.end_date) if li.end_date else "",
                "advertiser_id": campaign.client_campaign_ID or "",
                "target_cpm": li.unit_cost or "",  # unit_cost → target_cpm
                "target_ctr": li.ctr or "",
                "target_cpc": None,
                "booked_budget": None,
                "sitelist": "",
            }

    return Response(data)


@api_view(["POST"])
def publish_campaign_excel(request, campaign_id):
    report_type = request.data.get("report_type", "cpm")
    try:
        excel_obj = CampaignExcel.objects.get(
            campaign__campaign_id=campaign_id, report_type=report_type
        )
    except CampaignExcel.DoesNotExist:
        return Response({"error": "Excel not found. Generate first."}, status=404)

    excel_obj.publish_status = "published"
    excel_obj.save(update_fields=["publish_status"])

    return Response(
        {
            "message": "Excel published successfully",
            "campaign_id": campaign_id,
            "report_type": report_type,
            "publish_status": excel_obj.publish_status,
        },
        status=200,
    )
