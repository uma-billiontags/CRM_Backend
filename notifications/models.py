from django.db import models
from clients.models import Client

# Create your models here.

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



