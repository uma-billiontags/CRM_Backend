# crm/pdf_templates.py

def build_io_html(campaign, client, io_id):
    line_items = campaign.line_items.all()
    contact = client.contacts.first() if client else None
    today = __import__('datetime').date.today().strftime('%d %B %Y')

    def fmt_date(d):
        if not d: return "—"
        return d.strftime('%d-%m-%Y')

    def fmt_date_long(d):
        if not d: return "—"
        return d.strftime('%d %B %Y')

    import json

    def parse_geo(geo):
        if not geo: return "—"
        try:
            data = json.loads(geo) if isinstance(geo, str) else geo
            parts = []
            for loc in (data if isinstance(data, list) else [data]):
                seg = ', '.join(filter(None, [
                    loc.get('country',''), loc.get('state',''), loc.get('city','')
                ]))
                if seg: parts.append(seg)
            return ' | '.join(parts) or "—"
        except Exception:
            return str(geo)

    line_rows = ""
    total_impressions = 0
    for i, li in enumerate(line_items):
        bg = "#fff" if i % 2 == 0 else "#f9fafb"
        impressions = li.impressions or 0
        total_impressions += impressions
        line_rows += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;
                     font-family:monospace;color:#4f46e5;">
            {io_id}/<br/>{li.line_item_id or "—"}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;">
            <div style="font-weight:600;color:#111827;">{campaign.campaign_name}</div>
            <div style="color:#6b7280;margin-top:2px;">{li.line_item_name or "—"}</div>
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;text-align:center;">
            {li.ad_format or "—"}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;text-align:center;">
            {', '.join(li.ethnicity) if li.ethnicity else "—"}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;
                     text-align:center;white-space:nowrap;">
            {fmt_date(li.start_date)}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;
                     text-align:center;white-space:nowrap;">
            {fmt_date(li.end_date)}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;text-align:right;">
            {f"{impressions:,}" if impressions else "—"}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;text-align:center;">
            {li.units or "—"}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;text-align:right;">
            {f"${float(li.unit_value):.2f}" if li.unit_value else (li.unit_cost or "—")}
          </td>
          <td style="padding:8px 10px;border:1px solid #e5e7eb;font-size:12px;
                     text-align:right;font-weight:600;">
            {li.unit_cost or "—"}
          </td>
        </tr>"""

    insertion_order = getattr(campaign, 'insertion_order', None)
    client_addr1 = client.address_line1 if client else "—"
    client_addr2 = client.address_line2 if client else "—"
    contact_name = contact.name if contact else "—"
    contact_phone = contact.phone if contact else (client.phone if client else "—")
    contact_email = contact.email if contact else (client.email if client else "—")
    advertiser = campaign.advertiser or (client.name if client else "—")
    payment_terms = (client.billing.payment_terms if hasattr(client, 'billing') and client.billing else "Post Payment – Net 30") if client else "Post Payment – Net 30"
    # CORRECT — get geo from first line item, or leave blank
    first_li = line_items[0] if line_items else None
    geo = parse_geo(first_li.geo_targeting if first_li else None)

    cpm_row = f"<tr><td>CPM</td><td>${campaign.new_cpm}</td></tr>" if campaign.new_cpm else ""
    price_row = f"<tr><td>Price</td><td>${campaign.new_price}</td></tr>" if campaign.new_price else ""
    notes_row = f"<tr><td>Notes</td><td>{campaign.notes}</td></tr>" if campaign.notes else ""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; color: #111827; background: #fff; }}
    .page {{ width:100%; margin: 0 auto; padding: 32px 36px; }}
    .header-bar {{ display: flex; justify-content: space-between; align-items: flex-start;
                   margin-bottom: 24px; border-bottom: 3px solid #111827; padding-bottom: 16px; }}
    .section-title {{ font-size: 11px; font-weight: 800; color: #374151;
                      text-transform: uppercase; letter-spacing: 0.08em;
                      border-bottom: 2px solid #111827; padding-bottom: 4px; margin: 20px 0 12px; }}
    .info-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 6px; }}
    .info-table td {{ padding: 5px 8px; border: 1px solid #e5e7eb; vertical-align: top; }}
    .info-table td:first-child {{ font-weight: 600; color: #374151; background: #f9fafb;
                                   width: 140px; white-space: nowrap; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .booking-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }}
    .booking-table th {{ padding: 8px 10px; background: #111827; color: #fff; font-weight: 700;
                         font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em;
                         border: 1px solid #374151; text-align: left; }}
    .booking-table th.right {{ text-align: right; }}
    .booking-table th.center {{ text-align: center; }}
    .total-row td {{ font-weight: 800; font-size: 13px; background: #f9fafb !important;
                     border-top: 2px solid #111827 !important; }}
    .sig-section {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
                    margin-top: 32px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
    .sig-box {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }}
    .sig-box-title {{ font-size: 11px; font-weight: 700; color: #374151;
                      text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px; }}
    .sig-line {{ border-bottom: 1px solid #9ca3af; margin: 28px 0 6px; }}
    .sig-meta {{ font-size: 11px; color: #6b7280; }}
    .tc-page {{ width: 100%; padding: 12px 20 40px; }}
    .tc-title {{ font-size: 15px; font-weight: 900; color: #111827;
                 margin-bottom: 6px; letter-spacing: -0.3px; }}
    .tc-subtitle {{ font-size: 12px; color: #374151; margin-bottom: 18px; font-style: italic; }}
    .tc-section-title {{ font-size: 12px; font-weight: 800; color: #111827;
                         margin: 18px 0 8px; text-decoration: underline; }}
    .tc-body {{ font-size: 12px; color: #374151; line-height: 1.75; }}
    .tc-body ol {{ padding-left: 20px; margin: 8px 0; }}
    .tc-body ol li {{ margin-bottom: 8px; }}
    .tc-body p {{ margin-bottom: 10px; }}
    @page {{ margin: 10mm; }}
  </style>
</head>
<body>
<div class="page">
  <div class="header-bar">
    <div>
      <div style="font-size:22px;font-weight:900;color:#111827;letter-spacing:-0.5px;">
        Billion<span style="color:#f59e0b;">tags</span>
      </div>
      <div style="font-size:10px;color:#6b7280;letter-spacing:0.08em;text-transform:uppercase;">
        Creations Pvt. Ltd.
      </div>
    </div>
    <div style="text-align:right;">
      <div>
        <div style="font-size:11px;color:#6b7280;font-weight:600;letter-spacing:0.05em;
                    text-transform:uppercase;">Booking IO ID</div>
        <div style="font-size:15px;font-weight:800;color:#111827;font-family:monospace;">
          {io_id}
        </div>
      </div>
      <div style="margin-top:6px;">
        <div style="font-size:11px;color:#6b7280;font-weight:600;letter-spacing:0.05em;
                    text-transform:uppercase;">Campaign ID</div>
        <div style="font-size:15px;font-weight:800;color:#111827;font-family:monospace;">
          {campaign.campaign_id}
        </div>
      </div>
    </div>
  </div>

  <div class="section-title">Publisher Details</div>
  <table class="info-table">
    <tr><td>Network / Publisher</td><td>Billiontags Creations Pvt. Ltd.</td></tr>
    <tr><td>Date of IO</td><td>{today}</td></tr>
    <tr><td>Order Taken By</td><td>Praveen Kumar</td></tr>
    <tr><td>Email</td><td>praveenkumar@billiontags.com</td></tr>
    <tr><td>Address</td>
      <td>Sankaran Avenue, Shree Vatsa Towers, No:1/93, Janakpuri 2nd Street,
          2nd Floor, Above Cars 24 Velachery, Chennai, Tamil Nadu 600042.</td></tr>
  </table>

  <div class="section-title">Customer Details</div>
  <div class="two-col">
    <div>
      <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;">
        Customer Contact Details
      </div>
      <table class="info-table">
        <tr><td>Agency / Advertiser</td><td>{advertiser}</td></tr>
        <tr><td>Phone</td><td>{contact_phone}</td></tr>
        <tr><td>E-Mail</td><td>{contact_email}</td></tr>
        <tr><td>Address Line – 1</td><td>{client_addr1}</td></tr>
        <tr><td>Address Line – 2</td><td>{client_addr2}</td></tr>
      </table>
    </div>
    <div>
      <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;">
        Customer Billing Details
      </div>
      <table class="info-table">
        <tr><td>Agency / Advertiser</td><td>{advertiser}</td></tr>
        <tr><td>Phone</td><td>{contact_phone}</td></tr>
        <tr><td>E-Mail</td><td>{contact_email}</td></tr>
        <tr><td>Address Line – 1</td><td>{client_addr1}</td></tr>
        <tr><td>Address Line – 2</td><td>{client_addr2}</td></tr>
      </table>
    </div>
  </div>

  <div class="section-title">Order Details</div>
  <div class="two-col">
    <div>
      <table class="info-table">
        <tr><td>Advertising Client Name</td>
            <td>{client.name if client else campaign.client_name}</td></tr>
        <tr><td>Campaign Name</td><td><strong>{campaign.campaign_name}</strong></td></tr>
        <tr><td>GEO</td><td>{geo}</td></tr>
        <tr><td>Client Campaign ID</td><td>{campaign.client_campaign_ID or "—"}</td></tr>
      </table>
    </div>
    <div>
      <table class="info-table">
        <tr><td>Payment Terms</td><td>{payment_terms}</td></tr>
        <tr><td>Out Clause</td><td>48 Hours</td></tr>
        <tr><td>Billing On</td><td>Billiontags Numbers</td></tr>
        <tr><td>Campaign Dates</td>
            <td>{fmt_date(campaign.start_date)} to {fmt_date(campaign.end_date)}</td></tr>
        {cpm_row}
        {price_row}
        {notes_row}
      </table>
    </div>
  </div>

  <div class="section-title">Booking Details</div>
  <table class="booking-table">
    <thead>
      <tr>
        <th style="width:110px;">IO ID &amp; Line Item ID</th>
        <th>IO Name &amp; Line Item Name</th>
        <th class="center">Ad Type</th>
        <th class="center">Ethnicity</th>
        <th class="center">Start Date</th>
        <th class="center">End Date</th>
        <th class="right">Volume</th>
        <th class="center">Unit</th>
        <th class="right">Unit Cost</th>
        <th class="right">Net Cost</th>
      </tr>
    </thead>
    <tbody>
      {line_rows or '<tr><td colspan="10" style="padding:16px;text-align:center;color:#9ca3af;">No line items</td></tr>'}
      <tr class="total-row">
        <td colspan="6" style="padding:8px 10px;border:1px solid #e5e7eb;
                                text-align:right;font-weight:800;">Total</td>
        <td style="padding:8px 10px;border:1px solid #e5e7eb;text-align:right;font-weight:800;">
          {total_impressions:,}
        </td>
        <td colspan="3" style="padding:8px 10px;border:1px solid #e5e7eb;"></td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">Signature</div>
  <div class="sig-section">
    <div class="sig-box">
      <div class="sig-box-title">Duly Authorized on behalf of Billiontags</div>
      <table style="width:100%;font-size:12px;">
        <tr><td style="color:#6b7280;width:80px;">Name:</td>
            <td style="font-weight:600;">Praveen Kumar</td></tr>
        <tr><td style="color:#6b7280;">Date:</td><td>{today}</td></tr>
      </table>
      <div class="sig-line"></div>
      <div class="sig-meta">Signature</div>
    </div>
    <div class="sig-box">
      <div class="sig-box-title">Duly Authorized on behalf of the Advertiser Agency</div>
      <table style="width:100%;font-size:12px;">
        <tr><td style="color:#6b7280;width:80px;">Name:</td>
            <td style="font-weight:600;">{contact_name}</td></tr>
        <tr><td style="color:#6b7280;">Date:</td><td>{today}</td></tr>
      </table>
      <div class="sig-line"></div>
      <div class="sig-meta">Signature</div>
    </div>
  </div>
</div>

<div style="page-break-before:always;"></div>
<div class="tc-page">
  <div class="tc-body">
    <div class="tc-title">BILLIONTAGS Terms and Conditions for Internet Advertising</div>
    <p class="tc-subtitle">
      These BILLIONTAGS, Inc. Terms and Conditions for Internet Advertising (“Standard Terms”) are affiliating
(“BILLIONTAGS”) the Advertiser / Agency identified below (“Advertiser” or “Agency”). The parties acknowledge and agree
the Standard Terms shall be effective as of the date set forth below, and shall govern one or more separate insertion
orders (each an “IO”) executed by the parties.
    </p>
    <div class="tc-section-title">Cancellation and Termination:</div>
    <ol>
      <li>At any time prior to the serving of the first impression of the IO, Agency may cancel the IO with reports must be
updated / sent /given access on a daily basis. Cancellation 48Hours prior written notice, without penalty.</li>
      <li>Upon the serving of the first impression of the IO, Agency may cancel the IO for any reason, without penalty, by
providing BILLIONTAGS written notice of cancellation which will be effective after the later of: (i) 30 days after
serving the first impression of the IO; or (ii) 14 days after providing BILLIONTAGS with such written notice."</li>
      <li>Either party may terminate an IO if the other party is in material breach not cured
          within 10 days after written notice.</li>
        <li>Non-breaching party, except as otherwise stated in this Agreement with regard to specific breaches. Additionally, if
Agency or Advertiser commit a violation of the same Policy (as defined below), where such Policy had been
provided by BILLIONTAGS to Agency, on three separate occasions after having received timely notice of each such
breach, even if such breach has been cured by Agency or Advertiser, then BILLIONTAGS may terminate the IO
associated with such breach upon written notice. If Agency or Advertiser do not cure a violation of a Policy within
the applicable ten-day cure period after written notice, where such Policy had been provided by BILLIONTAGS to
Agency, then BILLIONTAGS may terminate the IO associated with such breach upon written notice."</li>
      <li>Short rates will apply to cancel buys to the degree stated on the IO.</li>
      <li>For Any Creative or tags that is not in accordance with IAB Standard or a non performing creative or tags were
given to BILLIONTAGS then BILLIONTAGS cannot be accounted for non-performance however BILLIONTAGS can be
given another creative tags as an alternative. There will be a minimum deployment charge for all campaigns
irrespective of the completion or not and that will not be borne by BILLIONTAGS for any failure from the Advertiser
side. Deployment cost will be prorated according to the delivery report and is a sole discretion of BILLIONTAGS
However we will ensure that the campaigns is delivered in accordance to the IO.</li>
    </ol>
    <div class="tc-section-title">Refund Policy:</div>
    <p>BILLIONTAGS do not allow Redirects, Malware, Adult Ads and Pop ups. An Advertiser can only have one offer per
campaign. If an Advertiser wish to display two different Landing Pages for the same offer, then Billiontags requires two
tracking URL within the same campaign.</p>
    <p>"You are entitled to request for a refund in the following cases:
First, if there has been an incorrect payment transaction. Second, if you have made a prepayment and you prove that
the actions forming the basis of the pricing model of your Campaign are based on a Publisher’s fraudulent activities (i.e.
the artificial increase of actions). In order to detect and prove Publishers’ fraudulent activities you undertake to send to
Billiontags a weekly detailed report of sources/websites you consider to be fraudulent. In case the Publisher’s fraudulent
activities cannot be clearly identified based on your report, Billiontags is entitled to request additional proof from you. If
you fail to submit a weekly report or additional proof regarding the Publishers’ fraudulent activities, Billiontags may
refuse to give a refund and adjust your balance accordingly. In case you are using post-payment method and you are
able to prove Publishers’ fraudulent activities pursuant to this clause, Billiontags will not invoice you for the agreed
actions based on Publisher’s fraudulent activities. Third, if at the end of the validity of the Contract it appears that you
have spent for Billiontags services less than you have prepaid. In such a case you are entitled to ask for a refund within
30 days after the termination of the Contract, provided that the amount of your unused balance is at least 50 EUR.
Before refunding, Billiontags will have to finalize all not invoiced spending and make necessary adjustments where
needed. After finalizing all current statistics, your unused balance will be refunded to you at your request, minus an
administrative fee of 25% to cover Billiontags costs and fees related with the management of giving a refund, within 30
working days. YOUR REFUND WILL BE CREDITED BACK TO THE SAME PAYMENT METHOD AND SAME PAYMENT ACCOUNT
THAT YOU USED TO MAKE YOUR LAST PAYMENT. You may be required to provide additional information or
documentation in order for Billiontags to confirm your identity, before any refund request is processed. PLEASE BE
AWARE THAT IF YOUR CONTRACT WITH Billiontags IS TERMINATED DUE TO THE VIOLATION OF CONTRACT BY YOU (E.G.
DUE TO YOUR FRAUDULENT ACTIVITY), Billiontags IS ENTITLED TO A CONTRACTUAL PENALTY IN THE AMOUNT OF YOUR
UNUSED BALANCE AND THEREFORE, Billiontags MAY REFUSE TO GIVE YOU A REFUND BY WAY OF SET-OFF OF THE
CLAIMS.”</p>
  </div>
</div>
</body>
</html>"""


def build_invoice_html(campaign, client, invoice_obj=None, period_start=None, period_end=None):
    import json
    line_items = campaign.line_items.all()
    contact = client.contacts.first() if client else None

    today = __import__('datetime').date.today()
    invoice_date = today.strftime('%d %B %Y')

    # Invoice number
    invoice_number = invoice_obj.invoice_id if invoice_obj else f"BTU{campaign.id:06d}"

# Currency
    currency_code = (client.billing.billing_currency if hasattr(client, 'billing') and client.billing else "USD") if client else "USD"
    currency_map = {"INR": "₹", "AED": "د.إ", "NZD": "$", "USD": "$"}
    currency_symbol = currency_map.get(currency_code, "$")

    payment_terms = (client.billing.payment_terms if hasattr(client, 'billing') and client.billing else "NET 0 Days") if client else "NET 0 Days"

    # ── Use passed period dates (month slice) or fallback to full campaign dates
    p_start = period_start or campaign.start_date
    p_end = period_end or campaign.end_date

    period_start_str = p_start.strftime('%d %b %Y') if p_start else "—"
    period_end_str = p_end.strftime('%d %b %Y') if p_end else "—"

    # ── Pro-rata amount calculation per line item ──
    total_campaign_days = (campaign.end_date - campaign.start_date).days + 1
    slice_days = (p_end - p_start).days + 1

    subtotal = 0
    for li in line_items:
        cost_num = 0
        if li.unit_cost:
            try:
                cost_num = float(''.join(c for c in li.unit_cost if c.isdigit() or c == '.'))
            except ValueError:
                pass
        elif li.unit_value:
            cost_num = float(li.unit_value or 0)

        # Pro-rata: (full_cost / total_days) * days_in_this_month
        prorata = round((cost_num / total_campaign_days) * slice_days, 2) if total_campaign_days > 0 else cost_num
        subtotal += prorata

    discount = subtotal * 0.2
    total = subtotal - discount
    
    client_id_display = client.client_id if client else "—"
    contact_name = contact.name if contact else (client.name if client else "NILL")
    company_name = client.name if client else "—"
    address = client.address_line1 if client else "—"
    city_country = f"{client.city}, {client.country}" if client and client.city else (client.country if client else "—")
    vast_number = client.vast_number if client else "—"
    cin_number = client.cin_number if client else "—"

    booking_rows = ""
    total_impressions = 0
    for i, li in enumerate(line_items):
        bg = "#f9fafb" if i % 2 == 1 else "#fff"
        cost_num = 0
        if li.unit_cost:
            try:
                cost_num = float(''.join(c for c in li.unit_cost if c.isdigit() or c == '.'))
            except ValueError:
                pass
        elif li.unit_value:
            cost_num = float(li.unit_value or 0)

        vol = f"{li.impressions:,}" if li.impressions else "0"
        total_impressions += li.impressions or 0
        booking_io_id = f"BI{campaign.id:05d}"

        booking_rows += f"""
        <tr style="border-bottom:1px solid #e5e7eb;background:{bg};">
          <td style="padding:10px 12px;font-size:12px;color:#374151;vertical-align:top;line-height:1.6;">
            <div style="font-weight:600;color:#111827;margin-bottom:2px;">
              Advertiser: {campaign.advertiser or (client.name if client else "—")} |
              ID: {client_id_display}
            </div>
            <div style="color:#6b7280;">
              Campaign: {campaign.campaign_name} | ID: {campaign.campaign_id}
            </div>
            <div style="color:#6b7280;">Insertion Order ID: {booking_io_id}</div>
            <div style="color:#4f46e5;font-weight:500;">
              Line Item: {li.line_item_name or "—"} | ID: {li.line_item_id}
            </div>
          </td>
          <td style="padding:10px 12px;font-size:12px;text-align:center;white-space:nowrap;">
            <div style="font-size:10px;color:#6b7280;font-weight:600;">CLIENT</div>
            <div style="font-weight:700;color:#111827;font-family:monospace;">
              {campaign.campaign_id}
            </div>
          </td>
          <td style="padding:10px 12px;font-size:12px;text-align:center;white-space:nowrap;">
            <span style="display:inline-block;padding:2px 8px;border-radius:4px;
                         background:#eef2ff;color:#4f46e5;font-weight:700;font-size:11px;">
              {li.units or "CPM"}
            </span>
          </td>
          <td style="padding:10px 12px;font-size:12px;text-align:right;white-space:nowrap;
                     font-weight:600;color:#111827;">
            {currency_symbol}{cost_num:.2f}
          </td>
          <td style="padding:10px 12px;font-size:12px;text-align:right;white-space:nowrap;">
            {vol}
          </td>
          <td style="padding:10px 12px;font-size:12px;text-align:right;white-space:nowrap;
                     font-weight:700;color:#111827;">
            {currency_symbol}{cost_num:.2f}
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; color: #111827; background: #fff; font-size: 13px; }}
    .page {{ width: 100%; padding: 16px 20px; }}
    .inv-header {{ display: flex; justify-content: space-between;
                   align-items: flex-start; margin-bottom: 32px; }}
    .inv-logo-text {{ font-size: 26px; font-weight: 900; color: #111827; letter-spacing:-1px; }}
    .inv-logo-text span {{ color: #f59e0b; }}
    .section-label {{ font-size: 11px; font-weight: 800; color: #374151;
                      text-transform: uppercase; letter-spacing: 0.08em;
                      border-bottom: 2px solid #111827; padding-bottom: 4px; margin: 20px 0 10px; }}
    .inv-top-grid {{ display: grid; grid-template-columns: 1fr 1fr;
                     gap: 24px; margin-bottom: 24px; }}
    .bill-to-label {{ font-size: 11px; font-weight: 800; color: #374151;
                      text-transform: uppercase; letter-spacing: 0.08em;
                      margin-bottom: 8px; border-bottom: 2px solid #111827; padding-bottom: 4px; }}
    .inv-detail-row {{ display: flex; justify-content: space-between;
                       padding: 4px 0; font-size: 12px; border-bottom: 1px solid #f3f4f6; }}
    .inv-detail-label {{ color: #6b7280; }}
    .inv-detail-val {{ font-weight: 600; color: #111827; }}
    .amount-due-box {{ background: #0f172a; border-radius: 10px; padding: 16px 20px;
                       margin-bottom: 20px; display: flex; justify-content: space-between;
                       align-items: center; }}
    .summary-box {{ border: 1px solid #e5e7eb; border-radius: 8px;
                    padding: 14px 16px; margin-bottom: 20px; }}
    .summary-row {{ display: flex; justify-content: space-between;
                    font-size: 12px; padding: 3px 0; }}
    .summary-row.total {{ font-weight: 800; font-size: 14px; color: #111827;
                          border-top: 1px solid #e5e7eb; margin-top: 6px; padding-top: 8px; }}
    .bank-table {{ width: 100%; font-size: 12px; border-collapse: collapse; }}
    .bank-table td {{ padding: 4px 8px; }}
    .bank-table td:first-child {{ color: #6b7280; font-weight: 600; width: 140px; }}
    .remittance-list {{ padding-left: 18px; font-size: 12px; color: #374151; line-height: 1.9; }}
    .booking-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }}
    .booking-table th {{ padding: 9px 12px; background: #111827; color: #fff; font-weight: 700;
                         font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em;
                         border: 1px solid #374151; text-align: left; }}
    .booking-table td {{ border: 1px solid #e5e7eb; word-break: break-word; }}
    .sig-box {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px 24px; width: 320px; }}
    @page {{ margin: 10mm; }}
  </style>
</head>
<body>

<!-- PAGE 1 -->
<div class="page">
  <div class="inv-header">
    <div>
      <div class="inv-logo-text">Billion<span>tags</span></div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:22px;font-weight:900;color:#111827;">Tax Invoice</div>
      <div style="font-size:13px;color:#6b7280;font-family:monospace;">
        Invoice number: {invoice_number}
      </div>
    </div>
  </div>

  <div style="display:flex;justify-content:flex-end;margin-bottom:24px;">
    <div style="text-align:right;font-size:12px;color:#6b7280;line-height:1.7;">
      <div style="font-size:13px;font-weight:700;color:#111827;">
        Billiontags Enterprises - FZCO
      </div>
      IFZA Business Park, DDP,<br/>
      Building A2, Premises No: 30485 - 001,<br/>
      Dubai, United Arab Emirates, Pin code: 341041.<br/>
      TRN No: 104101902500003<br/>
      License No: 30485
    </div>
  </div>

  <div class="inv-top-grid">
    <div>
      <div class="bill-to-label">Bill To</div>
      <div class="inv-detail-row">
        <strong><span class="inv-detail-label">Contact Person Name</span></strong>
        <span class="inv-detail-val">{contact_name}</span>
      </div>
      <div class="inv-detail-row">
        <strong><span class="inv-detail-label">Company Name</span></strong>
        <span class="inv-detail-val">{company_name}</span>
      </div>
      <div class="inv-detail-row">
        <strong><span class="inv-detail-label">Address</span></strong>
        <span class="inv-detail-val">{address}</span>
      </div>
      <div class="inv-detail-row">
        <strong><span class="inv-detail-label">Location</span></strong>
        <span class="inv-detail-val">{city_country}</span>
      </div>
      <div class="inv-detail-row">
        <strong><span class="inv-detail-label">VAST No</span></strong>
        <span class="inv-detail-val">{vast_number}</span>
      </div>
      <div class="inv-detail-row">
        <strong><span class="inv-detail-label">CIN No</span></strong>
        <span class="inv-detail-val">{cin_number}</span>
      </div>
    </div>
    <div>
      <div class="bill-to-label">Details</div>
      <div class="inv-detail-row">
        <span class="inv-detail-label">Invoice number</span>
        <span class="inv-detail-val">{invoice_number}</span>
      </div>
      <div class="inv-detail-row">
        <span class="inv-detail-label">Invoice date</span>
        <span class="inv-detail-val">{invoice_date}</span>
      </div>
      <div class="inv-detail-row">
        <span class="inv-detail-label">Payment terms</span>
        <span class="inv-detail-val">{payment_terms}</span>
      </div>
      <div class="inv-detail-row">
        <span class="inv-detail-label">Due date</span>
        <span class="inv-detail-val">{invoice_date}</span>
      </div>
    </div>
  </div>

  <div class="amount-due-box">
    <div>
      <div style="font-size:11px;color:#f59e0b;font-weight:700;letter-spacing:0.08em;">
        Pay in {currency_code}
      </div>
      <div style="font-size:12px;color:rgba(255,255,255,0.5);font-weight:600;
                  text-transform:uppercase;letter-spacing:0.08em;">Total amount due</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.4);margin-top:2px;">
        Due {invoice_date}
      </div>
    </div>
    <div style="font-size:28px;font-weight:900;color:#fff;letter-spacing:-1px;">
      {currency_symbol}{total:.1f}
    </div>
  </div>

  <div class="summary-box">
    <div style="font-size:11px;font-weight:800;color:#374151;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:10px;">
      Summary for {period_start_str} - {period_end_str}
    </div>
    <div class="summary-row"><span>Pay in {currency_code}</span><span></span></div>
    <div class="summary-row">
      <span>Sub Total</span><span>{currency_symbol} {subtotal:.1f}</span>
    </div>
    <div class="summary-row"><span>VAT (0%)</span><span>{currency_symbol}0.0</span></div>
    <div class="summary-row" style="color:#dc2626;">
      <span>Discount (20.0%)</span><span>- {currency_symbol}{discount:.0f}</span>
    </div>
    <div class="summary-row total">
      <span>Total amount due in {currency_code}</span>
      <span>{currency_symbol}{total:.1f}</span>
    </div>
  </div>

  <div class="section-label">Bank Account Details</div>
  <table class="bank-table">
    <tr><td>Name</td><td>Billiontags Enterprises FZCO</td></tr>
    <tr><td>Account Number</td><td>1000000000001</td></tr>
    <tr><td>Bank</td><td>Emirates Bank</td></tr>
    <tr><td>Swift Code</td><td>EBUAAEAD</td></tr>
    <tr><td>IBAN No</td><td>AE321021000101500019001</td></tr>
    <tr><td>Bank Address</td><td>Emirates Bank PJSC. P.O. Box: 777, Dubai, UAE</td></tr>
  </table>

  <div style="font-size:12px;font-weight:700;color:#111827;margin:16px 0 8px;">
    Remittance instructions:
  </div>
  <ul class="remittance-list">
    <li>To ensure that we correctly match your payment, always reference invoice numbers when making your payment.</li>
    <li>If paying for multiple invoices, send an email to finance@billiontags.com with your company name and total payment
amount in the subject line, and list the invoice numbers and respective amounts in the email</li>
    <li>Please send your payments only to the bank account listed below on this official Billiontags invoice.</li>
  </ul>
</div>

<!-- PAGE 2 — Booking Details -->
<div style="page-break-before:always;"></div>
<div class="page">
  <div class="inv-header" style="margin-bottom:20px;">
    <div>
      <div class="inv-logo-text">Billion<span>tags</span></div>
      <div style="font-size:10px;color:#6b7280;letter-spacing:0.08em;">Enterprises - FZCO</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:22px;font-weight:900;color:#111827;">Tax Invoice</div>
      <div style="font-size:13px;color:#6b7280;font-family:monospace;">
        Invoice number: {invoice_number}
      </div>
    </div>
  </div>

  <div class="section-label">Booking Details</div>
  <table class="booking-table">
    <thead>
      <tr>
        <th style="width:42%;">Description</th>
        <th style="text-align:center;width:13%;">Client Campaign Id</th>
        <th style="text-align:center;width:8%;">Metrics</th>
        <th style="text-align:right;width:10%;">Unit Cost</th>
        <th style="text-align:right;width:10%;">Volume</th>
        <th style="text-align:right;width:12%;">Amount {currency_symbol}</th>
      </tr>
    </thead>
    <tbody>
      {booking_rows or '<tr><td colspan="6" style="padding:20px;text-align:center;color:#9ca3af;">No line items</td></tr>'}
      <tr style="background:#f9fafb;font-weight:800;">
        <td colspan="3" style="padding:9px 12px;border:1px solid #e5e7eb;text-align:right;">
          Subtotal in {currency_code}
        </td>
        <td style="padding:9px 12px;border:1px solid #e5e7eb;"></td>
        <td style="padding:9px 12px;border:1px solid #e5e7eb;text-align:right;">
          {total_impressions:,}
        </td>
        <td style="padding:9px 12px;border:1px solid #e5e7eb;text-align:right;">
          {currency_symbol}{subtotal:.1f}
        </td>
      </tr>
      <tr style="background:#0f172a;">
        <td colspan="5" style="padding:10px 12px;border:1px solid #374151;
                                text-align:right;font-weight:800;color:#fff;">
          Total amount due in {currency_code}
        </td>
        <td style="padding:10px 12px;border:1px solid #374151;text-align:right;
                   font-weight:900;font-size:15px;color:#fff;">
          {currency_symbol}{total:.1f}
        </td>
      </tr>
    </tbody>
  </table>
</div>

<!-- PAGE 3 — Signature -->
<div style="page-break-before:always;"></div>
<div class="page">
  <div class="inv-header" style="margin-bottom:20px;">
    <div>
      <div class="inv-logo-text">Billion<span>tags</span></div>
      <div style="font-size:10px;color:#6b7280;letter-spacing:0.08em;">Enterprises - FZCO</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:22px;font-weight:900;color:#111827;">Tax Invoice</div>
      <div style="font-size:13px;color:#6b7280;font-family:monospace;">
        Invoice number: {invoice_number}
      </div>
    </div>
  </div>

  <div class="section-label">Bank Account Details</div>
  <table class="bank-table">
    <tr><td>Name</td><td>Billiontags Enterprises FZCO</td></tr>
    <tr><td>Account Number</td><td>1000000000001</td></tr>
    <tr><td>Bank</td><td>Emirates Bank</td></tr>
    <tr><td>Swift Code</td><td>EBUAAEAD</td></tr>
    <tr><td>IBAN No</td><td>AE321021000101500019001</td></tr>
    <tr><td>Bank Address</td><td>Emirates Bank PJSC. P.O. Box: 777, Dubai, UAE</td></tr>
  </table>

  <div style="display:flex;justify-content:flex-end;margin-top:48px;">
    <div class="sig-box">
      <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:12px;">
        Duly Authorized on behalf of the Billiontags Enterprises - FZCO by:
      </div>
      <div style="font-size:13px;color:#111827;margin-bottom:8px;">
        Name: <strong>Praveen Kumar</strong>
      </div>
      <div style="font-size:12px;color:#6b7280;">Designation: Director</div>
      <div style="border-bottom:1px solid #9ca3af;margin:32px 0 8px;"></div>
      <div style="font-size:11px;color:#6b7280;">Signature</div>
    </div>
  </div>
</div>

</body>
</html>"""