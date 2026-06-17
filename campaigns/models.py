from django.db import models
from clients.models import Client

# Create your models here.

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

    dv_id = models.CharField(max_length=100, blank=True, null=True, unique=True)  # ← ADD THIS

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

