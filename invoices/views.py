from django.shortcuts import render
from weasyprint import HTML as WeasyHTML
from django.core.files.base import ContentFile
from .pdf_templates import build_invoice_html
from .models import Invoice
from rest_framework.response import Response
from rest_framework.decorators import api_view
from campaigns.models import Campaign
from clients.models import Client
from django.http import FileResponse
import calendar
from datetime import date

# ── Helper: split campaign date range into monthly slices ─────────────────────
def split_into_months(start_date, end_date):
    """
    Returns list of (slice_start, slice_end) tuples, one per month.
    Example: 2/6/2026 → 10/7/2026
    Returns: [(2/6/2026, 30/6/2026), (1/7/2026, 10/7/2026)]
    """
    slices = []
    current_start = start_date

    while current_start <= end_date:
        # Last day of current month
        last_day = calendar.monthrange(current_start.year, current_start.month)[1]
        month_end = current_start.replace(day=last_day)

        # Slice end is whichever comes first: month end or campaign end
        slice_end = min(month_end, end_date)
        slices.append((current_start, slice_end))

        # Move to 1st of next month
        if slice_end == end_date:
            break
        if current_start.month == 12:
            current_start = current_start.replace(year=current_start.year + 1, month=1, day=1)
        else:
            current_start = current_start.replace(month=current_start.month + 1, day=1)

    return slices


# ── Helper: pro-rata amount for a line item in a date slice ───────────────────
def calculate_prorata_amount(li, campaign_start, campaign_end, slice_start, slice_end):
    """
    Calculates pro-rata cost for a line item for a given month slice.
    Formula: (total_cost / total_campaign_days) * days_in_slice
    """
    # Get line item cost
    cost_num = 0
    if li.unit_cost:
        try:
            cost_num = float(''.join(c for c in li.unit_cost if c.isdigit() or c == '.'))
        except ValueError:
            pass
    elif li.unit_value:
        cost_num = float(li.unit_value or 0)

    total_days = (campaign_end - campaign_start).days + 1
    slice_days = (slice_end - slice_start).days + 1

    if total_days == 0:
        return cost_num

    return round((cost_num / total_days) * slice_days, 2)


# ── Generate Invoice PDFs (one per month) ─────────────────────────────────────
@api_view(['POST'])
def generate_invoice_pdf(request, campaign_id):
    try:
        campaign = Campaign.objects.select_related('client').prefetch_related(
            'line_items'
        ).get(campaign_id=campaign_id)
    except Campaign.DoesNotExist:
        return Response({'error': 'Campaign not found'}, status=404)

    if campaign.approval_status != 'approved':
        return Response({'error': 'Campaign is not approved'}, status=400)

    if not campaign.start_date or not campaign.end_date:
        return Response({'error': 'Campaign has no start/end date'}, status=400)

    try:
        client = Client.objects.select_related(
            'billing', 'ownership'
        ).prefetch_related('contacts').get(pk=campaign.client.pk)
    except Client.DoesNotExist:
        client = None

    # ── Split campaign into monthly slices ──
    slices = split_into_months(campaign.start_date, campaign.end_date)

    generated_invoices = []

    for slice_start, slice_end in slices:
        # Check if invoice already exists for this month slice — skip if yes
        existing = Invoice.objects.filter(
            campaign=campaign,
            invoice_from=slice_start,
            invoice_to=slice_end
        ).first()

        if existing and existing.pdf_file:
            generated_invoices.append({
                'invoice_id': existing.invoice_id,
                'invoice_from': str(slice_start),
                'invoice_to': str(slice_end),
                'download_url': request.build_absolute_uri(existing.pdf_file.url),
                'skipped': True,
            })
            continue

        # Create invoice record for this month
        if not existing:
            invoice_obj = Invoice.objects.create(
                campaign=campaign,
                client=campaign.client,
                invoice_from=slice_start,
                invoice_to=slice_end,
            )
        else:
            invoice_obj = existing

        # Build HTML with pro-rata amounts for this slice
        html_string = build_invoice_html(
            campaign, client,
            invoice_obj=invoice_obj,
            period_start=slice_start,
            period_end=slice_end,
        )
        pdf_bytes = WeasyHTML(string=html_string).write_pdf()

        filename = f"{invoice_obj.invoice_id}_{campaign_id}_{slice_start.strftime('%Y%m')}.pdf"
        invoice_obj.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

        generated_invoices.append({
            'invoice_id': invoice_obj.invoice_id,
            'invoice_from': str(slice_start),
            'invoice_to': str(slice_end),
            'download_url': request.build_absolute_uri(invoice_obj.pdf_file.url),
            'skipped': False,
        })

    return Response({
        'message': f'{len(generated_invoices)} invoice(s) generated successfully',
        'invoices': generated_invoices,
    }, status=200)


# ── Download Invoice PDF by invoice_id ────────────────────────────────────────
@api_view(['GET'])
def download_invoice_pdf(request, invoice_id):
    try:
        invoice_obj = Invoice.objects.get(invoice_id=invoice_id)
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


# ── Get campaigns + their invoices for a client ───────────────────────────────
@api_view(['GET'])
def get_invoice_list_by_client(request, client_id):
    campaigns = Campaign.objects.select_related('client').filter(
        client__client_id=client_id,
        approval_status='approved',
    ).prefetch_related('invoices', 'line_items').order_by('-created_at')

    data = []
    for c in campaigns:
        invoices = c.invoices.all().order_by('invoice_from')
        invoice_list = []
        for inv in invoices:
            invoice_list.append({
                'invoice_id': inv.invoice_id,
                'invoice_from': str(inv.invoice_from) if inv.invoice_from else '',
                'invoice_to': str(inv.invoice_to) if inv.invoice_to else '',
                'pdf_generated': bool(inv.pdf_file),
                'pdf_url': request.build_absolute_uri(inv.pdf_file.url) if inv.pdf_file else None,
            })

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
            'invoices':         invoice_list,
            'all_generated':    len(invoice_list) > 0 and all(i['pdf_generated'] for i in invoice_list),
            'created_at':       c.created_at.isoformat() if c.created_at else '',
        })

    return Response(data)


# ── Get all clients (for dropdown) ────────────────────────────────────────────
@api_view(['GET'])
def get_all_clients(request):
    clients = Client.objects.filter(status='approved').values(
        'client_id', 'name'
    ).order_by('name')
    return Response(list(clients))