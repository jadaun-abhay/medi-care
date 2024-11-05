from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from users.manager import CustomUserManager

class Roles(models.Model):
    role = models.TextField()
    state = models.TextField()

    class Meta:
        db_table = "roles"

class CustomUser(AbstractUser):

    def nameFile(self, filename):
        return '/'.join([f"{self.role.role}", f"id-{self.id}", filename])

    username = None
    email = models.CharField(max_length = 60, unique = True)
    phone_number = models.CharField(max_length = 10)
    role = models.ForeignKey(Roles, on_delete = models.SET_NULL, null = True)
    profile_photo = models.ImageField(upload_to = nameFile, default = '/'.join(["default_profile", "profile.jpeg"]))

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
    role = models.ForeignKey(Roles, on_delete = models.SET_NULL, null = True)

    class Meta:
        db_table = "left_panel"

