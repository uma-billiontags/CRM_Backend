from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from datetime import datetime
import os

# ==============================
# CUSTOM USER MODEL 
# ==============================
class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('client', 'Client'),
        ('creative', 'Creative'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Link user to client
    client = models.ForeignKey('Client', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20,default='active')

    def __str__(self):
        return self.username


# ==============================
# CLIENT ID GENERATOR
# ==============================
def generate_client_id():
    year = datetime.now().year
    last = Client.objects.filter(client_id__contains=str(year)).order_by('id').last() # Get last client of current year

    if last:
        last_num = int(last.client_id.split('-')[-1]) # Extract last number from ID (00005 → 5)
        new_num = last_num + 1 # Increment (eg: 5 ---> 5+1 = 6)
    else:
        new_num = 1 #  or else create the first client of the year

    return f"CLT-{year}-{str(new_num).zfill(5)}"  # CLT-2026-00001


# ==============================
# CLIENT (MAIN TABLE)
# ==============================
class Client(models.Model):
    client_id = models.CharField(max_length=20, unique=True, editable=False) # here auto generate ID and cannot edit

    # Basic Info
    name = models.CharField(max_length=200) # enter company name
    #reporting_id = models.CharField(max_length=100)

    company_type = models.CharField(max_length=100)
    agency_type = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=200, blank=True)

    website = models.URLField(blank=True)

    phone = models.CharField(max_length=20)
    email = models.EmailField()

    billing_currency = models.CharField(max_length=20, default="INR")
    #industry = models.CharField(max_length=100, blank=True)

    address_line1 = models.TextField()
    address_line2 = models.TextField(blank=True)

    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)

    cin_number = models.CharField(max_length=50)
    vast_number = models.CharField(max_length=100)
    #gst_number = models.CharField(max_length=50, blank=True)

    place_of_supply = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True) # It tells whether a client is active or inactive.

    created_at = models.DateTimeField(auto_now_add=True) 

    # In your Client model, add:
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def save(self, *args, **kwargs):  # Auto ID save
        if not self.client_id:   # it checks the client is already have an ID
            self.client_id = generate_client_id()
        super().save(*args, **kwargs)  # save() is a built-in Django method

    def __str__(self):
        return f"{self.name} ({self.client_id})"


# ==============================
# BILLING & COMMERCIALS
# ==============================
class ClientBilling(models.Model):
    #client = models.OneToOneField(Client, on_delete=models.CASCADE) related_name means access the data
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='billing') #  that links one record in a model to exactly one record in another


    #pricing_model = models.CharField(max_length=100)
    #agency_fee_type = models.CharField(max_length=100)
    #agency_fee_value = models.FloatField()

    #minimum_billing_amount = models.FloatField(null=True, blank=True)

    credit_period_days = models.IntegerField()
    payment_type = models.CharField(max_length=50)

    payment_terms = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=50)

    tds_applicable = models.BooleanField(default=False)
    tds_section = models.CharField(max_length=50)

    credit_limit = models.FloatField()
    outstanding_limit = models.FloatField()

    billing_currency = models.CharField(max_length=20, default="INR")
    billing_contact = models.CharField(max_length=100)

    advance_amount = models.FloatField()

    def __str__(self):
        return f"Billing - {self.client.name}"
    

# ==============================
# CLIENT ADDRESSES (MULTIPLE)
# ==============================


class CompanyAddress(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="addresses") # it means one client have multiple addresses

    address_line1 = models.TextField()
    address_line2 = models.TextField(blank=True)

    country = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)

    is_primary = models.BooleanField(default=False) # Is this the main (primary) address or not?

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Whenever you fetch data, show the latest records first. - (minus sign) → descending order ---> (latest - oldest)

    def __str__(self):
        return f"{self.client.name} - {self.address_line1[:30]}"


# ==============================
# CLIENT CONTACTS (MULTIPLE)
# ==============================


class CompanyContact(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contacts")

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    designation = models.CharField(max_length=100)

    country = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)
    address_line1 = models.TextField()
    address_line2 = models.TextField(blank=True)
    #digital_signature = models.TextField(null=True, blank=True)
    digital_signature = models.FileField(upload_to="signatures/", null=True, blank=True) # it stores in media folder/signatures/image.png

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # it always shows the newest records first

    def __str__(self):
        return f"{self.name} - {self.client.name}"

# ==============================
# OPERATIONAL SETUP
# ==============================
# class ClientOperational(models.Model):
#     client = models.OneToOneField(Client, on_delete=models.CASCADE)

#     default_market = models.CharField(max_length=100)
#     default_platform = models.CharField(max_length=100)

#     inventory_type = models.CharField(max_length=100)
#     campaign_objective = models.CharField(max_length=100)

#     language = models.CharField(max_length=50)
#     audience_focus = models.CharField(max_length=200, blank=True)
#     ethnicity = models.CharField(max_length=100, blank=True)

#     ad_formats = models.CharField(max_length=200)
#     timezone = models.CharField(max_length=50)

#     def __str__(self):
#         return f"Operational - {self.client.name}"


# ==============================
# ACCOUNT OWNERSHIP
# ==============================
class ClientOwnership(models.Model):
    #client = models.OneToOneField(Client, on_delete=models.CASCADE)
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='ownership')


    account_manager = models.CharField(max_length=100)
    sales_owner = models.CharField(max_length=100)
    campaign_manager = models.CharField(max_length=100)
    finance_owner = models.CharField(max_length=100)

    def __str__(self):
        return f"Ownership - {self.client.name}"


# ==============================
# CLASSIFICATION
# ==============================
class ClientClassification(models.Model):
    #client = models.OneToOneField(Client, on_delete=models.CASCADE)
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='classification')

    client_type = models.CharField(max_length=100)
    priority = models.CharField(max_length=50)
    risk_level = models.CharField(max_length=50)

    payment_behavior = models.CharField(max_length=100)

    avg_response_time = models.IntegerField()

    notes = models.TextField(blank=True)

    additional_internal_notes = models.CharField(max_length=500, blank=True, null=True)
    additional_tags = models.CharField(max_length=400, blank=True, null=True)

    


    def __str__(self):
        return f"Classification - {self.client.name}"
    



# --------------------------------------------------------------------------------


# ==============================
# CAMPAGIN MODEL 
# ==============================

class Campaign(models.Model):

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="campaigns")

    advertiser = models.CharField(max_length=200)
    website_url = models.URLField(blank=True, null=True)

    campaign_name = models.CharField(max_length=300)

    client_campaign_ID = models.CharField(max_length=100, blank=True, null=True)
    purchase_order_ID = models.CharField(max_length=100, blank=True, null=True)

    campaign_type = models.CharField(max_length=50)
    buying_type = models.CharField(max_length=60)
    objective = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    # Auto-generated field
    campaign_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)

    approval_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved')],
        default='pending'
    )
        
    notes = models.TextField(blank=True, null=True)

    new_cpm = models.FloatField(null=True, blank=True)
    new_price = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    # ==================== CAMPAIGN ID GENERATOR (CA00001) ====================
    def generate_campaign_id(self):
        # Get the highest campaign_id starting with 'CA'
        last_campaign = Campaign.objects.filter(
            campaign_id__startswith='CA'
        ).order_by('-campaign_id').first()

        if last_campaign and last_campaign.campaign_id:
            try:
                # Extract number part: CA00123 → 123
                last_num = int(last_campaign.campaign_id[2:])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"CA{str(new_num).zfill(5)}"   # CA00001, CA00002, ...

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self): 
        return f"{self.campaign_name} ({self.campaign_id or 'Pending'})"
# ==== Add Line Item ====

class LineItem(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='line_items') # One campaign have multiple line items (,null=True, blank=True)

    line_item_id = models.CharField(max_length=50, unique=True)
    line_item_name = models.CharField(max_length=300)

    # Better than comma-separated
    ethnicity = models.JSONField(blank=True, null=True)

    start_date = models.DateField() 
    end_date = models.DateField()

    # multiple formats (image, video)
    ad_format = models.JSONField()

    impressions = models.BigIntegerField(null=True, blank=True)

    #landing_page = models.URLField(blank=True, null=True)
    
    units = models.CharField(max_length=100,null=True, blank=True)
    ctr = models.FloatField(null=True, blank=True)
    viewability = models.FloatField(null=True, blank=True)
    vcr = models.FloatField(null=True, blank=True)

    # add unit costs and kpi notes
    unit_cost = models.CharField(max_length=100,null=True, blank=True)
    kpi_notes = models.TextField(null=True, blank=True)
    unit_value = models.FloatField(null=True, blank=True)

    # ── NEW targeting fields ──
    age = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(max_length=100, blank=True, null=True)
    geo_targeting = models.TextField(blank=True, null=True)
    platforms = models.CharField(max_length=300, blank=True, null=True)
    frequency_cap = models.PositiveIntegerField(blank=True, null=True)
    brand_safety = models.CharField(max_length=20, blank=True, null=True)   

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    #  validation
    def clean(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError("End date must be greater than start date")

    def __str__(self):
        return f"{self.line_item_name} ({self.campaign.campaign_name})"


# ------------------------------------------------------------------

class Creative(models.Model):
    line_item = models.ForeignKey(
        LineItem,
        on_delete=models.CASCADE,
        related_name='creatives_detail' 
    )

    creative_name = models.CharField(max_length=300)

    # FILES
    main_asset = models.FileField(upload_to='creatives/main/', blank=True, null=True)
    #backup_image = models.FileField(upload_to='creatives/backup/', blank=True, null=True)

    # AUTO FILE TYPE
    #file_type = models.CharField(max_length=20, blank=True)

    # META DATA
    dimensions = models.CharField(max_length=50, blank=True)
    aspect_ratio = models.CharField(max_length=20, blank=True)
    file_size = models.CharField(max_length=30, blank=True)

    # FILE NAMES
    #main_asset_name = models.CharField(max_length=255, blank=True)
    #backup_image_name = models.CharField(max_length=255, blank=True)

    # EXTRA
    click_through_url = models.URLField(max_length=400, blank=True, null=True)
    appended_html_tag = models.TextField(blank=True)
    integration_code = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    creative_id = models.CharField(max_length=100, blank=True, null=True)  # ← ADD THIS

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.creative_name} ({self.line_item.line_item_name})"



# ==============================
# THIRD PARTY CREATIVE
# ==============================

class ThirdPartyCreative(models.Model):

    line_item = models.ForeignKey(LineItem,on_delete=models.CASCADE,related_name='third_party_creatives')
    # ZIP / HTML / TXT / DOCX / XLSX
    input_file = models.FileField(upload_to='thirdparty/files/',blank=True,null=True)

    # Backup image
    backup_image = models.FileField(upload_to='thirdparty/backup/',blank=True,null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    creative_id = models.CharField(max_length=100, blank=True, null=True)  # ← ADD THIS

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"ThirdPartyCreative ({self.line_item.line_item_name})"


# ------------------------------------------------------------------------- 

# -------- Team Access Model -----------

class TeamAccess(models.Model):


    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    member = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    password = models.CharField(max_length=255)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.member


# ==============================
# FCM TOKEN MODEL
# ==============================

class FCMToken(models.Model):

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    token = models.CharField(max_length=500, unique=True)
    #token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.token




# # ==============================
# # CHAT ROOM MODEL
# # ==============================

class ChatRoom(models.Model):

    campaign = models.OneToOneField(
        Campaign,
        on_delete=models.CASCADE,
        related_name='chat_room'
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room → {self.campaign.campaign_id} ({self.client.name})"


# # ==============================
# # MESSAGE MODEL
# # ==============================

class Message(models.Model):

    SENDER_TYPE = [
        ('client', 'Client'),
        ('admin',  'Admin'),
    ]
    
    MESSAGE_TYPE = [
        ('text',  'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file',  'File'),
    ]

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPE
    )

    content = models.TextField(blank=True)  # ← make blank=True (file messages may have no text)
    
    # ── NEW FIELDS ──────────────────────────
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE,
        default='text'
    )

    file = models.FileField(
        upload_to='chat/files/',
        null=True,
        blank=True
    )
     
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=50, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']  # oldest first → WhatsApp style

    def __str__(self):
        return f"{self.sender_type} → {self.room} → {self.timestamp:%Y-%m-%d %H:%M}"
    
    
class InsertionOrder(models.Model):
    io_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='insertion_orders')
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='insertion_order')
    pdf_file = models.FileField(upload_to='insertion_orders/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_io_id(self):
        last = InsertionOrder.objects.order_by('-id').first()
        if last and last.io_id:
            try:
                last_num = int(last.io_id[2:])  # Strip "IO" → get number
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1
        return f"IO{str(new_num).zfill(5)}"  # IO00001, IO00002...

    def save(self, *args, **kwargs):
        if not self.io_id:
            self.io_id = self.generate_io_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.io_id} → {self.campaign.campaign_id}"
    
    
class Invoice(models.Model):
    invoice_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='invoice')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    def generate_invoice_id(self):
        last = Invoice.objects.order_by('-id').first()
        if last and last.invoice_id:
            try:
                last_num = int(last.invoice_id[3:])  # Strip "BTU" → get number
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1
        return f"BTU{str(new_num).zfill(6)}"  # BTU000001, BTU000002...

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            self.invoice_id = self.generate_invoice_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_id} → {self.campaign.campaign_id}"
    


class CampaignExcel(models.Model):
    REPORT_TYPE_CHOICES = [
        ('cpm', 'CPM (Impressions Booked)'),
        ('cpc', 'CPC (Clicks Booked)'),
    ]
    campaign = models.ForeignKey(  # Change OneToOne → ForeignKey
        Campaign, on_delete=models.CASCADE, related_name='excel_reports'
    )
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, default='cpm')
    excel_file = models.FileField(upload_to='excel_reports/')
    generated_at = models.DateTimeField(auto_now=True)
    
     # ✅ Store per-line-item overrides as JSON
    # Format: { "LIBILL003": { "impressions": 50000, "start_date": "2026-06-01", ... } }
    line_item_overrides = models.JSONField(default=dict, blank=True)
    
    PUBLISH_STATUS_CHOICES = [
        ('published', 'Published'),
    ]
    publish_status = models.CharField(
        max_length=20,
        choices=PUBLISH_STATUS_CHOICES,
        null=True,
        blank=True,
        default=None
    )

    class Meta:
        unique_together = ('campaign', 'report_type')  # one CPM + one CPC per campaign
        
class CampaignLineItemExcel(models.Model):
    """
    Stores Excel-specific data for each line item.
    Linked to both Campaign and LineItem.
    """
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='line_item_excel_data'
    )
    line_item = models.OneToOneField(
        LineItem, on_delete=models.CASCADE, related_name='excel_data'
    )
    report_type = models.CharField(
        max_length=10,
        choices=[('cpm', 'CPM'), ('cpc', 'CPC')],
        default='cpm'
    )

    # ── Excel-specific fields ──
    impressions = models.BigIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    units = models.CharField(max_length=100, null=True, blank=True)
    ctr = models.FloatField(null=True, blank=True)
    viewability = models.FloatField(null=True, blank=True)
    vcr = models.FloatField(null=True, blank=True)
    kpi_notes = models.TextField(null=True, blank=True)
    sitelist = models.TextField(null=True, blank=True)  # ← only here, not in LineItem

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('line_item', 'report_type')

    def __str__(self):
        return f"ExcelData — {self.line_item.line_item_id} ({self.report_type})"