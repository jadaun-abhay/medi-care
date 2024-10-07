from django.db import models

# Create your models here.

from users.models import CustomUser

class DoctorInfo(models.Model):
    doctor = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, null = True)
    gender = models.CharField(max_length = 6)
    speciality = models.TextField()
    address = models.TextField()

    class Meta:
        db_table = "doctor_info"
