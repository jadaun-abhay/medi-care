from django.shortcuts import render

# Create your views here.

import json
from users.models import CustomUser
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out
from doctor.models import DoctorInfo, Speciality
from patient.models import Appointment
import datetime
from .models import LeftPanel

def index(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        panel_obj = LeftPanel.objects.filter(for_receptionist = True).values("title", "state", "priority", "icon")
        res = {"message" : "success", "data" : {"title" : "RECEPTIONIST", "children" : []}}
        for option in panel_obj:
            optn_dict = {}
            title = option.get("title")
            optn_dict["title"] = title
            state = option.get("state")
            optn_dict["state"] = state
            priority = option.get("priority")
            optn_dict["priority"] = priority
            icon = option.get("icon")
            optn_dict["icon"] = icon
            res["data"]["children"].append(optn_dict)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        user_obj = CustomUser.objects.filter(email = email).values("is_doctor", "is_patient", "is_superuser")
        if user_obj is None or not user_obj:
            res = {"message" : "User is not registered"}
            return JsonResponse(res, status = 401)
        is_doctor = user_obj[0].get("is_doctor")
        is_patient = user_obj[0].get("is_patient")
        is_receptionist = user_obj[0].get("is_superuser")
        user = authenticate(email = email, password = password)
        if user:
            l_in(request, user)
            res = {"message" : "Login is successfull", "data" : {"is_patient" : is_patient, "is_doctor" : is_doctor, "is_receptionist" : is_receptionist}}
            return JsonResponse(res, status = 200)
        else:
            res = {"message" : "Incorrect password"}
            return JsonResponse(res, status = 401)
    elif request.method == 'GET':
        if request.user.is_authenticated:
            is_doctor = request.user.is_doctor
            is_patient = request.user.is_patient
            if is_doctor:
                name = request.user.first_name
                last_name = request.user.last_name
                if not last_name:
                    name = name + " " + last_name
                profile_image = request.user.doctorinfo_set.filter(doctor = request.user.id).values_list("profile_photo", flat = True)[0]
            elif is_patient:
                name = request.user.first_name
                last_name = request.user.last_name
                if not (last_name is None or last_name == ""):
                    name += " " + last_name
                profile_image = request.user.patientinfo_set.filter(patient = request.user.id).values_list("profile_photo", flat = True)[0]
            else:
                name = request.user.first_name
                last_name = request.user.last_name
                if not last_name:
                    name += " " + last_name
                profile_image = "/".join(["doctor", "default_profile", "profile.jpeg"])
            is_receptionist = request.user.is_superuser
            res = {"message" : "Login is successfull", "data" : {"is_patient" : is_patient, "is_doctor" : is_doctor, "is_receptionist" : is_receptionist}, "profile_data" : {"name" : name, "photo" : profile_image}}
            return JsonResponse(res, status = 200)
        else:
            res = {"message" : "Login is required"}
            return JsonResponse(res, status = 401)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def logout(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            l_out(request)
            res = {"message" : "Logout is successful"}
            return JsonResponse(res, status = 200)
        else:
            res = {"message" : "Login is required"}
            return JsonResponse(res, status = 401)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def speaciality_list(request):
    if request.method == "GET":
        speciality_obj = Speciality.objects.all().values()
        speciality_list = []
        for speciality in speciality_obj:
            speciality_list.append(speciality)
        res = {"message" : "success", "data" : list(speciality_list)}
        return JsonResponse(res, status = 200)
    elif request.method == "POST":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        if not request.user.is_superuser:
            res = {'message' : "Feature is only available for the Receptionist"}
            return JsonResponse(res, status = 403)
        data = request.POST
        speciality = data.get("speciality")
        study = data.get("study")
        related_image = request.FILES.get("image")
        description = data.get("description")
        speciality_obj = Speciality.objects.filter(speciality = speciality)
        if speciality_obj:
            res = {"message" : f"{speciality} already exists"}
            return JsonResponse(res, status = 409)
        Speciality.objects.create(speciality = speciality, study = study, related_image = related_image, description = description)
        res = {"message" : "Resource created successfully"}
        return JsonResponse(res, status = 201)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def get_doctors_under_specific_speciality(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required"}
            return JsonResponse(res, status = 401)
        speciality_id = request.GET.get("speciality_id")
        speciality = Speciality.objects.filter(id = speciality_id)
        if not speciality:
            res = {"message" : "Speciality is not known"}
            return JsonResponse(res, status = 404)
        speciality = speciality[0]
        doctor_obj = DoctorInfo.objects.filter(speciality = speciality)
        if not doctor_obj:
            res = {"message" : "There are no doctors under such specialization"}
            return JsonResponse(res, status = 404)
        res = {"message" : "success", "data" : []}
        for dr in doctor_obj:
            doc_dict = {}
            id = dr.doctor.id
            doc_dict["doctor_id"] = id
            email = dr.doctor.email
            doc_dict["email"] = email
            first_name = dr.doctor.first_name
            doc_dict["name"] = first_name
            last_name = dr.doctor.last_name
            if last_name == "":
                last_name = None
            else:
                doc_dict["name"] += " " + last_name
            gender = dr.gender
            doc_dict["gender"] = gender
            speciality = dr.speciality.speciality
            doc_dict["speciality"] = speciality
            fees = dr.fees
            doc_dict["fee"] = 500   #To be set
            profile_photo = dr.profile_photo
            doc_dict["photo"] = profile_photo.name
            res["data"].append(doc_dict)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)   

def appointments(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.is_staff:
        res = {"message" : "Feature is only available for the receptionist"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        appointment_obj = Appointment.objects.filter(rejection_status = False, cure_status = False)
        res = {"message" : "success", "data" : {"approved_appointments" : [], "non_approved_appointments" : []}}
        for appointment in appointment_obj:
            apntmnt_dict = {}
            appointment_id = appointment.id
            apntmnt_dict["appointment_id"] = appointment_id
            patient_id = appointment.patient.id
            apntmnt_dict["patient_id"] = patient_id
            patient_name = appointment.patient.first_name
            last_name = appointment.patient.last_name
            if last_name:
                patient_name += " " + last_name
            apntmnt_dict["patient_name"] = patient_name
            problem = appointment.problem_description
            apntmnt_dict["problem_description"] = problem
            approval_status = appointment.approval_status
            apntmnt_dict["receptionist_approval_status"] = approval_status
            symptoms = appointment.symptoms
            apntmnt_dict["symptoms"] = symptoms
            date_time = appointment.requested_at.strftime("%d/%b/%Y at %H:%M:%S")
            apntmnt_dict["applied_at"] = date_time
            requested_for = appointment.requested_for.strftime("%d/%b/%Y at %H:%M:%S")
            apntmnt_dict["requested_for"] = requested_for
            last_name = appointment.preferred_doctor.last_name
            doctor_name = appointment.preferred_doctor.first_name
            if last_name:
                doctor_name += " " + last_name
            apntmnt_dict["preferred_doctor_name"] = doctor_name
            speciality = appointment.preferred_doctor.doctorinfo_set.reverse()[0].speciality.speciality
            apntmnt_dict["doctor_speciality"] = speciality
            if appointment.approval_status:
                res["data"]["approved_appointments"].append(apntmnt_dict)
            else:
                res["data"]["non_approved_appointments"].append(apntmnt_dict)
        return JsonResponse(res ,status = 200)
    elif request.method == "PATCH":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        appointment_obj = Appointment.objects.filter(id = appointment_id, payment = False)[0]
        if not appointment_obj:
            res = {"message" : "There are no such appointments with such id"}
            return JsonResponse(res, status = 202)
        elif appointment_obj.cure_status:
            res = {"message" : "Patient is already approved to meet to the doctor"}
            return JsonResponse(res, status = 400)
        else:
            approval_status = appointment_obj.approval_status
            requested_for = appointment_obj.requested_for
        if approval_status:
            res = {"message" : "Appointment is one step behind to be confirmed by doctor"}
            return JsonResponse(res, status = 406)
        else:
            is_doctor_free = Appointment.objects.filter(cure_status = True, preferred_doctor = appointment_obj.preferred_doctor, rejection_status = 0, requested_for = requested_for, payment = False, prescription_status = False)
            if not is_doctor_free:
                Appointment.objects.filter(id = appointment_id).update(approval_status = True, last_modified_by_receptionist = datetime.datetime.now())
                res = {"message" : "Appointment is approved and sent to doctor for his/her approval"}
                return JsonResponse(res, status = 201)
            else:
                Appointment.objects.filter(id = appointment_id).update(approval_status = False, remark = f"Already have an appointment fixed on {requested_for}", last_modified_by_receptionist = datetime.datetime.now())
                res = {"message" : f"Doctor is not avaiable on {requested_for.strftime("%d/%b/%Y at %H:%M:%S")}"}
                return JsonResponse(res, status = 400)
    elif request.method == "DELETE":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        remark = data.get("remark")
        if not remark:
            res = {"message" : "Remark is required !!!"}
            return JsonResponse(res, status = 400)
        appointment_obj = Appointment.objects.filter(id = appointment_id)[0]
        if appointment_obj.cure_status:
            res = {"message" : "The appointment has been confirmed by the doctor"}
            return JsonResponse(res, status = 400)
        Appointment.objects.filter(id = appointment_id).update(remark = remark, last_modified_by_receptionist = datetime.datetime.now(), rejection_status = True)
        res = {"message" : f"Appointment with appointment id = {appointment_id} has been rejected"}
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
        
