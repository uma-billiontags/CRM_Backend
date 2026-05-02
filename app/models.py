from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime




# ==============================
# CUSTOM USER
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
    last = Client.objects.filter(client_id__contains=str(year)).order_by('id').last()

    if last:
        last_num = int(last.client_id.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"CLT-{year}-{str(new_num).zfill(5)}"


# ==============================
# CLIENT (MAIN TABLE)
# ==============================
class Client(models.Model):
    client_id = models.CharField(max_length=20, unique=True, editable=False)

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

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.client_id:
            self.client_id = generate_client_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.client_id})"


# ==============================
# BILLING & COMMERCIALS
# ==============================
class ClientBilling(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE)

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
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="addresses")

    address_line1 = models.TextField()
    address_line2 = models.TextField(blank=True)

    country = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)

    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

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
    digital_signature = models.FileField(upload_to="signatures/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

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
    client = models.OneToOneField(Client, on_delete=models.CASCADE)

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
    client = models.OneToOneField(Client, on_delete=models.CASCADE)

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
from django.db import models, transaction
from datetime import datetime

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

    # ✅ Auto-generated field
    campaign_id = models.CharField(
        max_length=100,
        unique=True,
        editable=False
    )

    notes = models.TextField(blank=True, null=True)

    age = models.CharField(max_length=50)
    gender = models.CharField(max_length=50)

    geo_targeting = models.TextField()
    platforms = models.CharField(max_length=300)

    frequency_cap = models.PositiveIntegerField(blank=True, null=True)
    brand_safety = models.CharField(max_length=20)
    viewability_goal = models.PositiveIntegerField(blank=True, null=True)

    budget_type = models.CharField(max_length=10)
    total_budget = models.DecimalField(max_digits=14, decimal_places=2)

    start_date = models.DateField()
    end_date = models.DateField()

    pacing = models.CharField(max_length=20)
    day_parting = models.CharField(max_length=50, blank=True, null=True)
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    # ✅ Validation
    def clean(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError("End date must be greater than start date")

    # ✅ FIXED generator
    def generate_campaign_id(self):
        year = datetime.now().year

        last = Campaign.objects.filter(
            campaign_id__startswith=f"CMP-{year}"
        ).order_by('id').last()

        if last and last.campaign_id:
            last_num = int(last.campaign_id.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"CMP-{year}-{str(new_num).zfill(5)}"

    # ✅ FIXED save method (INSIDE CLASS)
    def save(self, *args, **kwargs):
        if not self.campaign_id:
            for i in range(5):
                with transaction.atomic():
                    new_id = self.generate_campaign_id()
                    if not Campaign.objects.filter(campaign_id=new_id).exists():
                        self.campaign_id = new_id
                        break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.campaign_name} ({self.client.name})"