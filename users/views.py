from django.shortcuts import render

# Create your views here.

import json
from users.models import CustomUser
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out
from doctor.models import DoctorInfo

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
            is_receptionist = request.user.is_superuser
            res = {"message" : "Login is successfull", "data" : {"is_patient" : is_patient, "is_doctor" : is_doctor, "is_receptionist" : is_receptionist}}
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
    
def get_speaciality_list(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        speciality_obj = DoctorInfo.objects.all().values_list("speciality", flat = True)
        speciality_set = set()
        for speciality in speciality_obj:
            speciality_set.add(speciality)
        res = {"message" : "success", "data" : list(speciality_set)}
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def get_doctors_under_specific_speciality(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required"}
            return JsonResponse(res, status = 401)
        data = json.loads(request.body)
        chosen_speciality = data.get("speciality")
        doctor_obj = DoctorInfo.objects.filter(speciality = chosen_speciality)
        if not doctor_obj:
            res = {"message" : "Chosen speciality does not exist"}
            return JsonResponse(res, status = 404)
        res = {"message" : "success", "data" : []}
        for dr in doctor_obj:
            doc_dict = {}
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
            res["data"].append(doc_dict)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
        

