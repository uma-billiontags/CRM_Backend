from django.shortcuts import render
from weasyprint import HTML as WeasyHTML
from django.core.files.base import ContentFile
from .pdf_templates import build_io_html, build_invoice_html
from .models import Invoice
from django.core.mail import send_mail
from rest_framework.response import Response 
from rest_framework.decorators import api_view, parser_classes
from .models import Client, Campaign
from django.http import FileResponse
from .serializers import Invoice

# Create your views here.

# ── Generate Invoice PDF ─────────────────────────────────────────────────────
@api_view(['POST'])
def generate_invoice_pdf(request, campaign_id):
    try:
        campaign = Campaign.objects.select_related(
            'client', 'invoice'
        ).prefetch_related(
            'line_items__creatives_detail',
            'line_items__third_party_creatives',
        ).get(campaign_id=campaign_id)
    except Campaign.DoesNotExist:
        return Response({'error': 'Campaign not found'}, status=404)

    # ── Check approval ──
    if campaign.approval_status != 'approved':
        return Response({'error': 'Campaign is not approved'}, status=400)

    # ── Check end date has passed ──
    from datetime import date
    if not campaign.end_date:
        return Response({'error': 'Campaign has no end date'}, status=400)

    if campaign.end_date > date.today():
        return Response({
            'error': 'Invoice cannot be generated before campaign end date',
            'end_date': str(campaign.end_date)
        }, status=400)

    # ── Get or create invoice record ──
    invoice_obj, _ = Invoice.objects.get_or_create(
        campaign=campaign,
        defaults={'client': campaign.client}
    )

    # ── Fetch client details ──
    try:
        client = Client.objects.select_related(
            'billing', 'ownership'
        ).prefetch_related('contacts').get(pk=campaign.client.pk)
    except Client.DoesNotExist:
        client = None

    # ── Build HTML and convert to PDF ──
    html_string = build_invoice_html(campaign, client)
    pdf_bytes = WeasyHTML(string=html_string).write_pdf()

    # ── Save PDF to model ──
    filename = f"{invoice_obj.invoice_id}_{campaign_id}.pdf"
    invoice_obj.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

    url = request.build_absolute_uri(invoice_obj.pdf_file.url)
    return Response({
        'message': 'Invoice PDF generated successfully',
        'invoice_id': invoice_obj.invoice_id,
        'download_url': url,
    }, status=200)


# ── Download saved Invoice PDF ───────────────────────────────────────────────
@api_view(['GET'])
def download_invoice_pdf(request, campaign_id):
    try:
        invoice_obj = Invoice.objects.get(campaign__campaign_id=campaign_id)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=404)

    if not invoice_obj.pdf_file:
        return Response({'error': 'PDF not generated yet'}, status=404)

    response = FileResponse(
        invoice_obj.pdf_file.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{invoice_obj.invoice_id}.pdf"'
    return response


# ── ADD THIS to your views.py ──────────────────────────────────────────────────

@api_view(['GET'])
def get_invoice_list_by_client(request, client_id):
    """
    Returns all approved campaigns for a client where end_date has passed,
    with their Invoice/PDF status.
    GET /get_invoice_list_by_client/<client_id>/
    """
    from datetime import date as date_today

    campaigns = Campaign.objects.select_related(
        'client', 'invoice'
    ).filter(
        client__client_id=client_id,
        approval_status='approved',
        end_date__lte=date_today.today(),   # only campaigns whose end date has passed
    ).prefetch_related('line_items').order_by('-created_at')

    data = []
    for c in campaigns:
        inv = getattr(c, 'invoice', None)
        data.append({
            'campaign_id':      c.campaign_id,
            'campaign_name':    c.campaign_name,
            'advertiser':       c.advertiser or '',
            'client_name':      c.client.name if c.client else '',
            'client_id':        c.client.client_id if c.client else '',
            'start_date':       str(c.start_date) if c.start_date else '',
            'end_date':         str(c.end_date) if c.end_date else '',
            'campaign_type':    c.campaign_type or '',
            'line_items_count': c.line_items.count(),
            'invoice_id':       inv.invoice_id if inv else None,
            # pdf_generated = Invoice exists AND has a pdf_file saved
            'pdf_generated':    bool(inv and inv.pdf_file),
            'pdf_url':          request.build_absolute_uri(inv.pdf_file.url) if inv and inv.pdf_file else None,
            'created_at':       c.created_at.isoformat() if c.created_at else '',
        })

    return Response(data)

