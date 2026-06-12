from django.shortcuts import render
from weasyprint import HTML as WeasyHTML
from django.core.files.base import ContentFile
from ...insertion_order.pdf_templates import build_io_html, build_invoice_html
from ...insertion_order.models import InsertionOrder
from ...insertion_order.models import Invoice


# Create your views here.


# ── Generate IO PDF ──────────────────────────────────────────────────────────
@api_view(['POST'])
def generate_io_pdf(request, campaign_id):
    try:
        # CORRECT — use select_related for OneToOne
        campaign = Campaign.objects.select_related(
            'client', 'insertion_order'
        ).prefetch_related(
            'line_items__creatives_detail',
            'line_items__third_party_creatives',
        ).get(campaign_id=campaign_id)
    except Campaign.DoesNotExist:
        return Response({'error': 'Campaign not found'}, status=404)

    # Get or create IO record
    io_obj, _ = InsertionOrder.objects.get_or_create(
        campaign=campaign,
        defaults={'client': campaign.client}
    )

    # Fetch client details
    try:
        client = Client.objects.select_related(
            'billing', 'ownership'
        ).prefetch_related('contacts').get(pk=campaign.client.pk)
    except Client.DoesNotExist:
        client = None

    # Build HTML and convert to PDF
    html_string = build_io_html(campaign, client, io_obj.io_id)
    pdf_bytes = WeasyHTML(string=html_string).write_pdf()

    # Save PDF to model
    filename = f"{io_obj.io_id}_{campaign_id}.pdf"
    io_obj.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

    url = request.build_absolute_uri(io_obj.pdf_file.url)
    return Response({
        'message': 'IO PDF generated successfully',
        'io_id': io_obj.io_id,
        'download_url': url,
    }, status=200)

# ── Download saved IO PDF ────────────────────────────────────────────────────
@api_view(['GET'])
def download_io_pdf(request, campaign_id):
    try:
        io_obj = InsertionOrder.objects.get(campaign__campaign_id=campaign_id)
    except InsertionOrder.DoesNotExist:
        return Response({'error': 'IO not found'}, status=404)

    if not io_obj.pdf_file:
        return Response({'error': 'PDF not generated yet'}, status=404)

    response = FileResponse(
        io_obj.pdf_file.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{io_obj.io_id}.pdf"'
    return response


@api_view(['GET'])
def get_io_list_by_client(request, client_id):
    """
    Returns all approved campaigns for a client with their IO/PDF status.
    GET /get_io_list_by_client/<client_id>/
    """
    campaigns = Campaign.objects.select_related(
        'client', 'insertion_order'
    ).filter(
        client__client_id=client_id,
        approval_status='approved'
    ).prefetch_related('line_items').order_by('-created_at')

    data = []
    for c in campaigns:
        io = getattr(c, 'insertion_order', None)
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
            'io_id':            io.io_id if io else None,
            # pdf_generated = IO exists AND has a pdf_file saved
            'pdf_generated':    bool(io and io.pdf_file),
            'pdf_url':          request.build_absolute_uri(io.pdf_file.url) if io and io.pdf_file else None,
            'created_at':       c.created_at.isoformat() if c.created_at else '',
        })

    return Response(data)


