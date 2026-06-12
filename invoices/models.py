from django.db import models
from clients.models import Client
from campaigns.models import Campaign

# Create your models here.

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
    
