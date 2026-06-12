from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('client', 'Client'),
        ('creative', 'Creative'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # ✅ Use full app_label.ModelName since Client is in another app
    client = models.ForeignKey(
        'clients.Client',        # ← was 'Client', now 'clients.Client'
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return self.username


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