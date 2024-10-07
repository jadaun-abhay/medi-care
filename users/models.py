from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from users.manager import CustomUserManager

class CustomUser(AbstractUser):
    username = None
    email = models.CharField(max_length = 60, unique = True)
    phone_number = models.CharField(max_length = 10)
    is_patient = models.BooleanField(null = True, blank = True)
    is_doctor = models.BooleanField(null = True, blank = True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = "medicare_users"


