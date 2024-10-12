from django.db import models

# Create your models here.
from users.models import CustomUser
from doctor.models import PaymentDetails

class PatientInfo(models.Model):

    def nameFile(self, filename):
        return '/'.join(["patient", f"id_{self.patient.id}", filename])
    
    patient = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, null = True)
    height = models.PositiveSmallIntegerField()
    weight = models.PositiveSmallIntegerField()
    dob = models.DateField()
    blood_group = models.CharField(max_length = 3)
    gender = models.CharField(max_length = 6)
    address = models.TextField()
    medical_history = models.TextField(null = True)
    profile_photo = models.ImageField(upload_to = nameFile, default = '/'.join(["patient", "default_profile", "profile.jpeg"]))

    class Meta:
        db_table = "patient_info"

class Appointment(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, null = True)
    preferred_doctor = models.ForeignKey(CustomUser, on_delete = models.SET_NULL, limit_choices_to = {"is_doctor" : True}, related_name = "doctor", null = True)
    symptoms = models.TextField()
    problem_description = models.TextField()
    requested_at = models.DateTimeField(auto_now_add = True)
    requested_for = models.DateTimeField(null = True)
    approval_status = models.BooleanField(default = False)
    cure_status = models.BooleanField(default = False)
    remark = models.TextField(null = True)
    last_modified_by_receptionist = models.DateTimeField(null = True)
    last_modiefied_by_doctor = models.DateTimeField(null = True)
    payment = models.ForeignKey(PaymentDetails, on_delete = models.SET_NULL, null = True)

    class Meta:
        db_table = "patient_appointment"

class Prescription(models.Model):
    appointment = models.ManyToManyField(Appointment)
    medicine = models.TextField()
    frequency = models.TextField()
    number_of_days = models.SmallIntegerField()

    class Meta:
        db_table = "prescription_details"
    