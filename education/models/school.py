from django.db import models

from system.models import BaseModel


class School(BaseModel):
    name = models.CharField(max_length=50)
    serial_number = models.CharField(max_length=6)  # SLxxxx

    def __str__(self) -> str:
        return self.name
