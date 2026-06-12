from django.db import models


class Location(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouse_location"

    def __str__(self):
        return self.code
