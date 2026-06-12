from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = EncryptedCharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = EncryptedCharField(max_length=500, blank=True)
    is_anonymized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crm_customer"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
