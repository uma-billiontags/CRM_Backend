from django.db import models
from datetime import datetime

# Create your models here.

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
    

