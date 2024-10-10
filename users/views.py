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

def index(request):
    if request.method == "GET":
        res = {"message" : "User app index A.P.I."}
        return JsonResponse(res, status = 200)
    
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
                print(name)
                last_name = request.user.last_name
                print(last_name)
                if not (last_name is None or last_name == ""):
                    name += " " + last_name
                    print(name)
                profile_image = request.user.patientinfo_set.filter(patient = request.user.id).values_list("profile_photo", flat = True)[0]
            else:
                name = request.user.first_name
                last_name = request.last_name
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
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        speciality_obj = Speciality.objects.all().values("speciality")
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
        related_image = data.get("image")
        description = data.get("description")
        speciality_obj = Speciality.objects.get(speciality = speciality)
        if not speciality_obj is None:
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
        data = json.loads(request.body)
        chosen_speciality = data.get("speciality_id")
        doctor_obj = DoctorInfo.objects.filter(speciality = chosen_speciality)
        if not doctor_obj:
            res = {"message" : "Chosen speciality does not exist"}
            return JsonResponse(res, status = 404)
        res = {"message" : "success", "data" : []}
        for dr in doctor_obj:
            doc_dict = {}
            id = dr.doctor.id
            doc_dict["doctor_id"] = id
            email = dr.doctor.email
            doc_dict["email"] = email
            first_name = dr.doctor.first_name
            doc_dict["first_name"] = first_name
            last_name = dr.doctor.last_name
            if last_name == "":
                last_name = None
            doc_dict["last_name"] = last_name
            gender = dr.gender
            doc_dict["gender"] = gender
            profile_photo = dr.profile_photo
            doc_dict["photo"] = profile_photo
            res["data"].append(doc_dict)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)   

def appointments(request):
    if request.method == "PATCH":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 405)
        if not request.user.is_superuser:
            res = {"message" : "Feature is only available for the Receptionist"}
            return JsonResponse(res, status = 403)
        data = json.loads(request.body)
        patient_id = data.get("patient_id")
        patient_obj = CustomUser.objects.get(id = patient_id)
        approval_status = patient_obj.appointment_set.get(patient = patient_id).approval_status
        if approval_status:
            res = {"message" : "Appointment is already confirmed by the receptionist"}
            return JsonResponse(res, status = 406)
        else:
            patient_obj.appointment_set.update(approval_status = True)
            res = {"message" : "Appointment is one step away from getting confirmed by the doctor"}
            return JsonResponse(res, status = 201)
    elif request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        if not request.user.is_superuser:
            res = {"message" : "Feature only available to the receptionist"}
            return JsonResponse(res, status = 403)
        appointment_obj = Appointment.objects.filter(cure_status = False)
        res = {"message" : "success", "data" : []}
        for appointment in appointment_obj:
            apntmnt_dict = {}
            patient_id = appointment.patient.id
            apntmnt_dict["patient_id"] = patient_id
            patient_name = appointment.patient.first_name + appointment.patient.last_name
            apntmnt_dict["patient_name"] = patient_name
            problem = appointment.problem_description
            approval_status = appointment.approval_status
            apntmnt_dict["receptionist_approval_status"] = approval_status
            apntmnt_dict["problem_description"] = problem
            symptoms = appointment.symptoms
            apntmnt_dict["symptoms"] = symptoms
            date_time = appointment.request_date_time
            apntmnt_dict["applied_at"] = date_time
            doctor_name = appointment.preferred_doctor.first_name + appointment.preferred_doctor.last_name
            apntmnt_dict["preferred_doctor_name"] = doctor_name
            doc_speciality = appointment.preferred_doctor.doctorinfo_set.speciality.speciality_set.values_list("speciality", flat = True)[0]
            apntmnt_dict["doctor_speciality"] = doc_speciality
            res["data"].append(apntmnt_dict)
        return JsonResponse(res ,status = 200)
    elif request.method == "DELETE":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required"}
            return JsonResponse(res, status = 401)
        if not request.user.is_superuser:
            res = {"message" : "Feature only avaiable to Receptionist"}
            return JsonResponse(res, status = 403)
        data = json.loads(request.body)
        patient_id = data.get("patient_id")
        remark = data.get("remark")
        patient_obj = CustomUser.objects.get(id = patient_id)
        patient_obj.appointment_set.update(remark = remark)
        
