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
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Link user to client
    client = models.ForeignKey('Client', on_delete=models.CASCADE, null=True, blank=True)

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
    reporting_id = models.CharField(max_length=100, blank=True)

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

    cin_number = models.CharField(max_length=50, blank=True)
    vast_number = models.CharField(max_length=100, blank=True, null=True)
    #gst_number = models.CharField(max_length=50, blank=True)

    place_of_supply = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True) # It tells whether a client is active or inactive.

    created_at = models.DateTimeField(auto_now_add=True)

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

    payment_terms = models.CharField(max_length=100, blank=True)
    tax_type = models.CharField(max_length=50, blank=True)

    tds_applicable = models.BooleanField(default=False)
    tds_section = models.CharField(max_length=50, blank=True)

    credit_limit = models.FloatField(null=True, blank=True)
    outstanding_limit = models.FloatField(null=True, blank=True)

    billing_currency = models.CharField(max_length=20, default="INR")
    billing_contact = models.CharField(max_length=100, blank=True)

    advance_amount = models.FloatField(null=True, blank=True)

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
    designation = models.CharField(max_length=100, blank=True)

    country = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=10, blank=True)
    address_line1 = models.TextField(blank=True)
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

    payment_behavior = models.CharField(max_length=100, blank=True)

    avg_response_time = models.IntegerField(null=True, blank=True)

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

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="campaigns") # link one client have multiple campagins

    advertiser = models.CharField(max_length=200)
    website_url = models.URLField(blank=True, null=True)

    campaign_name = models.CharField(max_length=300)

    client_campaign_ID = models.CharField(max_length=100, blank=True, null=True)
    purchase_order_ID = models.CharField(max_length=100, blank=True, null=True)

    campaign_type = models.CharField(max_length=50)
    buying_type = models.CharField(max_length=60)
    objective = models.CharField(max_length=100)

    # Auto-generated field

    campaign_id = models.CharField(max_length=100,unique=True,editable=False) # auto generate campaign ID 

    notes = models.TextField(blank=True, null=True)

    age = models.CharField(max_length=50)
    gender = models.CharField(max_length=50)

    geo_targeting = models.TextField()
    platforms = models.CharField(max_length=300)

    frequency_cap = models.PositiveIntegerField(blank=True, null=True)
    brand_safety = models.CharField(max_length=20)
    viewability_goal = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    #  FIXED generator
    def generate_campaign_id(self):
        year = datetime.now().year

        last = Campaign.objects.filter(campaign_id__startswith=f"CMP-{year}").order_by('id').last() # CMP-2026

        if last and last.campaign_id:     #  if last campaign id is CMP-2026-00025
            last_num = int(last.campaign_id.split('-')[-1]) # then split('-') → ['CMP', '2026', '00025'] & [-1] → '00025' & int(25)

            new_num = last_num + 1 # 25 + 1 = 26 
        else:
            new_num = 1 # or else it create first campaign of the year

        return f"CMP-{year}-{str(new_num).zfill(5)}"

    # FIXED save method (INSIDE CLASS)

    def save(self, *args, **kwargs):
        if not self.campaign_id:
           # to prevent duplicate IDs when multiple requests hit your server at the same time.
            for i in range(5): 
                with transaction.atomic():
                    new_id = self.generate_campaign_id()
                    if not Campaign.objects.filter(campaign_id=new_id).exists():
                        self.campaign_id = new_id
                        break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.campaign_name} ({self.client.name})"


# ==== Add Line Item ====

class LineItem(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='line_items', null=True, blank=True) # One campaign have multiple line items

    line_item_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    line_item_name = models.CharField(max_length=300)

    # Better than comma-separated
    ethnicity = models.JSONField(blank=True, null=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # multiple formats (image, video)
    ad_format = models.JSONField(blank=True, null=True)

    impressions = models.BigIntegerField(null=True, blank=True)

    landing_page = models.URLField(blank=True, null=True)
    
    units = models.BigIntegerField(null=True, blank=True)
    ctr = models.IntegerField(null=True, blank=True)
    viewability = models.IntegerField(null=True, blank=True)
    vcr = models.IntegerField(null=True, blank=True)

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


# # ===== CREATIVE =====
# class LineItemCreative(models.Model):
#     line_item = models.ForeignKey(
#         LineItem,
#         on_delete=models.CASCADE,
#         related_name='creatives'
#     )

#     file = models.FileField(upload_to='creatives/')
#     file_type = models.CharField(max_length=20, blank=True)  # image / video

#     created_at = models.DateTimeField(auto_now_add=True)

#     # Validation
#     def clean(self):
#         if self.file and self.file.size > 50 * 1024 * 1024:  # 50MB
#             raise ValueError("File too large")

#     #  Save method (MERGED correctly)
#     def save(self, *args, **kwargs):
#         # Validate first
#         self.full_clean()


# # Get file extension
#         # Detect file type
#         if self.file:
#             ext = os.path.splitext(self.file.name)[1].lower()

#             if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
#                 self.file_type = 'image'
#             elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
#                 self.file_type = 'video'
#             else:
#                 self.file_type = 'unknown'

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.line_item.line_item_name} - {self.file.name}"
    

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
    backup_image = models.FileField(upload_to='creatives/backup/', blank=True, null=True)

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
    click_through_url = models.URLField(blank=True, null=True)
    appended_html_tag = models.TextField(blank=True)
    integration_code = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    # AUTO DETECT FILE TYPE
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.creative_name} ({self.line_item.line_item_name})"







# class Creative(models.Model):
#     line_item = models.ForeignKey(
#         LineItem,
#         on_delete=models.CASCADE,
#         related_name='creatives'
#     )

#     creative_name = models.CharField(max_length=300)

#     # FILES
#     main_asset = models.FileField(upload_to='creatives/main/', blank=True, null=True)
#     backup_image = models.FileField(upload_to='creatives/backup/', blank=True, null=True)

#     # AUTO FILE TYPE
#     file_type = models.CharField(max_length=20, blank=True)

#     # META DATA
#     dimensions = models.CharField(max_length=50, blank=True)
#     aspect_ratio = models.CharField(max_length=20, blank=True)
#     file_size = models.CharField(max_length=30, blank=True)

#     # FILE NAMES
#     main_asset_name = models.CharField(max_length=255, blank=True)
#     backup_image_name = models.CharField(max_length=255, blank=True)

#     # EXTRA
#     click_through_url = models.URLField(blank=True, null=True)
#     appended_html_tag = models.TextField(blank=True)
#     integration_code = models.TextField(blank=True)
#     notes = models.TextField(blank=True)

#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-uploaded_at']

#     # AUTO DETECT FILE TYPE
#     def save(self, *args, **kwargs):
#         if self.main_asset:
#             ext = os.path.splitext(self.main_asset.name)[1].lower()

#             if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
#                 self.file_type = 'image'
#             elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
#                 self.file_type = 'video'
#             else:
#                 self.file_type = 'unknown'

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.creative_name} ({self.line_item.line_item_name})"


# serializer ()

# class LineItemSerializer(serializers.ModelSerializer):
#     creatives = CreativeSerializer(many=True, read_only=True)

#     class Meta:
#         model = LineItem
#         fields = '__all__'


# ---------------------------
# create campaign view function

# @api_view(['POST'])
# @parser_classes([MultiPartParser, FormParser])
# def create_campaign(request):

#     # 1. Validate client
#     client_id = request.data.get('client')

#     if not client_id:
#         return Response({"error": "client is required"}, status=400)

#     try:
#         client = Client.objects.get(client_id=client_id)
#     except Client.DoesNotExist:
#         return Response({"error": f"Client '{client_id}' not found"}, status=404)

#     # 2. Create Campaign
#     data = request.data.copy()
#     data.pop('client', None)

#     serializer = CampaignSerializer(data=data)

#     if not serializer.is_valid():
#         return Response(serializer.errors, status=400)

#     campaign = serializer.save(client=client)

#     # 3. Parse Line Items JSON
#     try:
#         line_items_data = json.loads(request.data.get('line_items', '[]'))
#     except Exception:
#         return Response({"error": "Invalid line_items JSON"}, status=400)

#     # 4. Create Line Items ONLY (no creatives here)
#     for li in line_items_data:
#         LineItem.objects.update_or_create(
#             line_item_id=li.get('line_item_id', ''),
#             defaults={
#                 'campaign': campaign,
#                 'line_item_name': li.get('lineItemName'),
#                 'ethnicity': li.get('ethnicity', []),
#                 'start_date': li.get('startDate') or None,
#                 'end_date': li.get('endDate') or None,
#                 'ad_format': li.get('adFormat', []),
#                 'impressions': li.get('impressions') or None,
#                 'landing_page': li.get('landingPage') or None,
#                 'units': li.get('units') or None,
#                 'ctr': li.get('ctr') or None,
#                 'viewability': li.get('viewability') or None,
#                 'vcr': li.get('vcr') or None,
#             }
#         )

#     return Response({
#         "message": "Campaign created successfully",
#         "campaign_id": campaign.campaign_id,
#         "data": CampaignSerializer(campaign).data
#     }, status=status.HTTP_201_CREATED)


# --------------------

# get campaigns

# @api_view(['GET'])
# def get_campaigns(request):

#     campaigns = Campaign.objects.select_related('client').prefetch_related(
#         Prefetch(
#             'line_items',
#             queryset=LineItem.objects.prefetch_related('creatives_detail')
#         )
#     ).all()

#     serializer = CampaignSerializer(campaigns, many=True)
#     return Response(serializer.data)


# --------------------

# get_campaigns_by_client

# @api_view(['GET'])
# def get_campaigns_by_client(request, client_id):

#     try:
#         campaigns = Campaign.objects.filter(
#             client__client_id=client_id
#         ).select_related('client').prefetch_related(
#             Prefetch(
#                 'line_items',
#                 queryset=LineItem.objects.prefetch_related('creatives_detail')
#             )
#         )

#         if not campaigns.exists():
#             return Response({"message": "No campaigns found for this client"}, status=404)

#         serializer = CampaignSerializer(campaigns, many=True)
#         return Response(serializer.data)

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)


# get campaign by id


# @api_view(['GET'])
# def get_campaign_by_id(request, campaign_id):

#     try:
#         campaign = Campaign.objects.select_related('client').prefetch_related(
#             Prefetch(
#                 'line_items',
#                 queryset=LineItem.objects.prefetch_related('creatives_detail')
#             )
#         ).get(campaign_id=campaign_id)

#     except Campaign.DoesNotExist:
#         return Response({"error": "Campaign not found"}, status=404)

#     serializer = CampaignSerializer(campaign)
#     return Response(serializer.data)