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

class LeftPanel(models.Model):
    title = models.CharField(max_length = 100)
    state = models.TextField()
    priority = models.SmallIntegerField()
    icon = models.TextField()
    for_patient = models.BooleanField(null = True)
    for_doctor = models.BooleanField(null = True)
    for_receptionist = models.BooleanField(null = True)

    class Meta:
        db_table = "left_panel"

