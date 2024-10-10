from django.db import models

# Create your models here.

from users.models import CustomUser

class Speciality(models.Model):

    def nameFile(self, filename):
        return '/'.join(["speciality", self.speciality, filename])
    
    speciality = models.TextField()
    study = models.TextField()
    description = models.TextField()
    related_image = models.ImageField(upload_to = nameFile)

    class Meta:
        db_table = "speciality_info"
    
class DoctorInfo(models.Model):

    def nameFile(self, filename):
        return '/'.join(["doctor", f"id_{self.doctor.id}", filename])
    
    doctor = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, null = True)
    speciality = models.ForeignKey(Speciality, on_delete = models.SET_NULL, null = True)
    gender = models.CharField(max_length = 6)
    address = models.TextField()
    profile_photo = models.ImageField(upload_to = nameFile, default = '/'.join(["doctor", "default_profile", "profile.jpeg"]))

    class Meta:
        db_table = "doctor_info"
