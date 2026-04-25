from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Client(models.Model):

    COUNTRY = [('India', 'India'), ('USA', 'USA'), ('UK', 'UK'), ('China', 'China')]
    BILLING_CURRENCY = [('INR', 'INR'), ('USD', 'USD')]
    PAYMENT_TYPE = [('Prepaid', 'Prepaid'), ('Postpaid', 'Postpaid')]
    PAYMENT_TERM = [('15 Days', '15 Days'), ('30 Days', '30 Days'), ('45 Days', '45 Days')]

    # CLIENT BASIC
    client_id = models.CharField(max_length=20, unique=True, editable=False)
    reporting_id = models.CharField(max_length=20, blank=True, null=True)

    client_name = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=10)
    email = models.EmailField()

    address_line1 = models.CharField(max_length=300)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=50, choices=COUNTRY)
    zipcode = models.CharField(max_length=10)

    # PAYMENT
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE)
    payment_term = models.CharField(max_length=20, choices=PAYMENT_TERM)
    billing_currency = models.CharField(max_length=10, choices=BILLING_CURRENCY)

    # TAX
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    cin_no = models.CharField(max_length=30, blank=True, null=True)

    # STATUS
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    # CONTACT
    contact_name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=10, blank=True, null=True)
    contact_email = models.EmailField()
    contact_country = models.CharField(max_length=100)
    contact_zipcode = models.CharField(max_length=20)
    contact_address_1 = models.CharField(max_length=300)
    contact_address_2 = models.CharField(max_length=300, blank=True, null=True)
    contact_designation = models.CharField(max_length=255, blank=True, null=True)
    #contact_signature = models.FileField(upload_to="signatures/")
    contact_signature = models.FileField(upload_to="signatures/",null=True,blank=True)

    # COMPANY ADDRESS
    company_address_line1 = models.CharField(max_length=300)
    company_address_line2 = models.CharField(max_length=300, blank=True, null=True)
    company_country = models.CharField(max_length=50, choices=COUNTRY)
    company_zipcode = models.CharField(max_length=10)

    # LOGIN
    user_email = models.EmailField(unique=True, blank=True, null=True)
    user_password = models.CharField(max_length=128, blank=True, null=True)

    # FIXED SAVE METHOD
    def save(self, *args, **kwargs):

        # Hash password
        if self.user_password and not self.user_password.startswith('pbkdf2_'):
            self.user_password = make_password(self.user_password)

        # Generate Client ID
        if not self.client_id:
            year = timezone.now().year

            last_client = Client.objects.filter(
                client_id__startswith=f"CLT-{year}-"
            ).order_by('id').last()

            if last_client:
                last_number = int(last_client.client_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.client_id = f"CLT-{year}-{new_number:05d}"

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.client_id} - {self.client_name}"



# CAMPAIGN TABLE



class Campaign(models.Model):

    # ── CHOICES ─────────────────────────────────────────────

    CAMPAIGN_TYPE_CHOICES = [
        ('Brand Awareness', 'Brand Awareness'),
        ('Performance', 'Performance'),
        ('Retargeting', 'Retargeting'),
        ('Prospecting', 'Prospecting'),
        ('Lead Generation', 'Lead Generation'),
    ]

    BUYING_TYPE_CHOICES = [
        ('Programmatic (DV360)', 'Programmatic (DV360)'),
        ('Direct', 'Direct'),
        ('Programmatic Guaranteed', 'Programmatic Guaranteed'),
        ('Preferred Deal', 'Preferred Deal'),
        ('Open Auction', 'Open Auction'),
    ]

    OBJECTIVE_CHOICES = [
        ('Increase Brand Awareness', 'Increase Brand Awareness'),
        ('Drive Website Traffic', 'Drive Website Traffic'),
        ('Generate Leads', 'Generate Leads'),
        ('Boost Sales', 'Boost Sales'),
        ('App Installs', 'App Installs'),
    ]

    PRIMARY_OBJ_CHOICES = [
        ('Reach', 'Reach'),
        ('Brand Awareness', 'Brand Awareness'),
        ('Traffic', 'Traffic'),
        ('Engagement', 'Engagement'),
        ('Video Views', 'Video Views'),
        ('Conversions', 'Conversions'),
    ]

    TARGET_AUDIENCE_CHOICES = [
        ('General Market', 'General Market'),
        ('Adults 18–35', 'Adults 18–35'),
        ('Women 25–45', 'Women 25–45'),
        ('Urban Youth', 'Urban Youth'),
        ('Custom Segment', 'Custom Segment'),
    ]

    BRAND_SAFETY_CHOICES = [
        ('Standard', 'Standard'),
        ('Strict', 'Strict'),
        ('Custom', 'Custom'),
    ]

    BUDGET_TYPE_CHOICES = [
        ('total', 'Total Budget'),
        ('daily', 'Daily Budget'),
    ]

    PACING_CHOICES = [
        ('Even', 'Even'),
        ('Front-Loaded', 'Front-Loaded'),
        ('Back-Loaded', 'Back-Loaded'),
        ('ASAP', 'ASAP'),
    ]

    DAY_PARTING_CHOICES = [
        ('All Day', 'All Day'),
        ('Business Hours (9am–6pm)', 'Business Hours (9am–6pm)'),
        ('Prime Time (6pm–11pm)', 'Prime Time (6pm–11pm)'),
        ('Custom', 'Custom'),
    ]

    TIMEZONE_CHOICES = [
        ('Asia/Kolkata (IST)', 'Asia/Kolkata (IST)'),
        ('UTC', 'UTC'),
        ('America/New_York (EST)', 'America/New_York (EST)'),
        ('Europe/London (GMT)', 'Europe/London (GMT)'),
    ]

    # ── STEP 1 : Client & Advertiser ───────────────────────

    client = models.CharField(max_length=200)
    advertiser = models.CharField(max_length=200)
    business_unit = models.CharField(max_length=200, blank=True, null=True)

    # ── STEP 2 : Campaign Details ──────────────────────────

    campaign_name = models.CharField(max_length=300)
    campaign_code = models.CharField(max_length=100, blank=True, null=True)
    campaign_type = models.CharField(max_length=50, choices=CAMPAIGN_TYPE_CHOICES)
    buying_type = models.CharField(max_length=60, choices=BUYING_TYPE_CHOICES)
    objective = models.CharField(max_length=100, choices=OBJECTIVE_CHOICES)

    kpis = models.CharField(max_length=500, blank=True, null=True)   # comma-separated
    notes = models.TextField(blank=True, null=True)

    # ── STEP 3 : Objectives & Settings ─────────────────────

    primary_objective = models.CharField(max_length=50, choices=PRIMARY_OBJ_CHOICES)
    target_audience = models.CharField(max_length=50, choices=TARGET_AUDIENCE_CHOICES)

    geo_targeting = models.CharField(max_length=500)   # e.g: "India,Chennai"
    platforms = models.CharField(max_length=500)       # e.g: "Google,Facebook"

    frequency_cap = models.PositiveIntegerField(blank=True, null=True)
    brand_safety = models.CharField(max_length=20, choices=BRAND_SAFETY_CHOICES)
    viewability_goal = models.PositiveIntegerField(blank=True, null=True)

    # ── STEP 4 : Budget & Schedule ─────────────────────────

    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES)
    total_budget = models.DecimalField(max_digits=14, decimal_places=2)

    start_date = models.DateField()
    end_date = models.DateField()

    pacing = models.CharField(max_length=20, choices=PACING_CHOICES)
    day_parting = models.CharField(max_length=50, choices=DAY_PARTING_CHOICES, blank=True, null=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, blank=True, null=True)

    # ── META ───────────────────────────────────────────────

    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    # ── VALIDATION ─────────────────────────────────────────

    def clean(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError("End date must be greater than start date")

    # ── STRING REPRESENTATION ──────────────────────────────

    def __str__(self):
        return f"{self.campaign_name} | {self.client} → {self.advertiser}"










'''
    def save(self, *args, **kwargs):
        if not self.client_id:
            year = timezone.now().year

            last_client = Client.objects.filter(
                client_id__startswith=f"CLT-{year}-"
            ).order_by('id').last()

            if last_client:
                last_number = int(last_client.client_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.client_id = f"CLT-{year}-{new_number:05d}"

        super().save(*args, **kwargs)

        def __str__(self):
            return f"{self.client_id} - {self.client_name}"
    '''
