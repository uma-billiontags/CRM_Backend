from django.shortcuts import render
from weasyprint import HTML as WeasyHTML
from django.core.files.base import ContentFile
from .pdf_templates import build_io_html, build_invoice_html
from .models import InsertionOrder
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Client, Campaign
from .serializers import InsertionOrderSerializer
from django.http import FileResponse


# ── Internal helper (no request, no decorator) ───────────────────────────────
def generate_io_for_campaign(campaign_id: str) -> str | None:
    """
    Called internally on approval to auto-generate the IO PDF.
    Returns io_id on success, None on failure.
    """
    try:
        campaign = (
            Campaign.objects.select_related("client", "insertion_order")
            .prefetch_related(
                "line_items__creatives_detail",
                "line_items__third_party_creatives",
            )
            .get(campaign_id=campaign_id)
        )

        io_obj, _ = InsertionOrder.objects.get_or_create(
            campaign=campaign, defaults={"client": campaign.client}
        )

        try:
            client = (
                Client.objects.select_related("billing", "ownership")
                .prefetch_related("contacts")
                .get(pk=campaign.client.pk)
            )
        except Client.DoesNotExist:
            client = None

        html_string = build_io_html(campaign, client, io_obj.io_id)
        pdf_bytes = WeasyHTML(string=html_string).write_pdf()

        filename = f"{io_obj.io_id}_{campaign_id}.pdf"
        io_obj.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

        print(f"✅ IO auto-generated: {io_obj.io_id}")
        return io_obj.io_id

    except Exception as e:
        import traceback
        print(f"⚠️ generate_io_for_campaign failed for {campaign_id}:")
        print(traceback.format_exc())
        return None


# ── API endpoint (has request, has decorator) ────────────────────────────────
@api_view(["POST"])
def generate_io_pdf(request, campaign_id):
    io_id = generate_io_for_campaign(campaign_id)
    if not io_id:
        return Response({"error": "Failed to generate IO PDF"}, status=500)

    try:
        io_obj = InsertionOrder.objects.get(campaign__campaign_id=campaign_id)
        url = request.build_absolute_uri(io_obj.pdf_file.url)
    except InsertionOrder.DoesNotExist:
        url = None

    return Response({
        "message": "IO PDF generated successfully",
        "io_id": io_id,
        "download_url": url,
    }, status=200)


# ── Download saved IO PDF ────────────────────────────────────────────────────
@api_view(["GET"])
def download_io_pdf(request, campaign_id):
    try:
        io_obj = InsertionOrder.objects.get(campaign__campaign_id=campaign_id)
    except InsertionOrder.DoesNotExist:
        return Response({"error": "IO not found"}, status=404)

    if not io_obj.pdf_file:
        return Response({"error": "PDF not generated yet"}, status=404)

    response = FileResponse(io_obj.pdf_file.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{io_obj.io_id}.pdf"'
    return response


# ── Get IO list by client ────────────────────────────────────────────────────
@api_view(["GET"])
def get_io_list_by_client(request, client_id):
    campaigns = (
        Campaign.objects.select_related("client", "insertion_order")
        .filter(client__client_id=client_id, approval_status="approved")
        .prefetch_related("line_items")
        .order_by("-created_at")
    )

    data = []
    for c in campaigns:
        io = getattr(c, "insertion_order", None)
        data.append({
            "campaign_id":      c.campaign_id,
            "campaign_name":    c.campaign_name,
            "advertiser":       c.advertiser or "",
            "client_name":      c.client.name if c.client else "",
            "client_id":        c.client.client_id if c.client else "",
            "start_date":       str(c.start_date) if c.start_date else "",
            "end_date":         str(c.end_date) if c.end_date else "",
            "campaign_type":    c.campaign_type or "",
            "line_items_count": c.line_items.count(),
            "io_id":            io.io_id if io else None,
            "pdf_generated":    bool(io and io.pdf_file),
            "pdf_url":          request.build_absolute_uri(io.pdf_file.url) if io and io.pdf_file else None,
            "created_at":       c.created_at.isoformat() if c.created_at else "",
        })

    return Response(data)