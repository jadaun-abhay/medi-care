from django.db import models

# Create your models here.
from users.models import CustomUser


class PatientInfo(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, null = True)
    height = models.PositiveSmallIntegerField()
    weight = models.PositiveSmallIntegerField()
    dob = models.DateField()
    blood_group = models.CharField(max_length = 3)
    gender = models.CharField(max_length = 6)
    address = models.TextField()

    class Meta:
        db_table = "patient_info"