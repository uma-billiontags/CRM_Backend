from django.db import models
from clients.models import Client
from campaigns.models import Campaign

# Create your models here.

   
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
    
    

