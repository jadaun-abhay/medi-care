from django.db import models

# Create your models here.

from users.models import CustomUser

class DoctorInfo(models.Model):

    def nameFile(self, filename):
        return '/'.join(["doctor", f"id_{self.doctor.id}", filename])
    
    doctor = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, null = True)
    gender = models.CharField(max_length = 6)
    speciality = models.TextField()
    address = models.TextField()
    profile_photo = models.ImageField(upload_to = nameFile, default = '/'.join(["doctor", "default_profile", "default.jpeg"]))

    class Meta:
        db_table = "doctor_info"
