from django.contrib import admin
from .models import User, Client, ClientBilling, ClientClassification, ClientOwnership, CompanyAddress, CompanyContact, Campaign


# Register your models here.
admin.site.register(User)
admin.site.register(Client)
admin.site.register(ClientBilling)
admin.site.register(ClientClassification)
admin.site.register(ClientOwnership)
admin.site.register(CompanyContact)
admin.site.register(CompanyAddress)
admin.site.register(Campaign)
