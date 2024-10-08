from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
from users.models import CustomUser
from users.manager import CustomUserManager 
import re
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out
import datetime

def index(request):
    if request.method == "GET":
        res = {"message" : "Patient related app first API"}
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)

def registration(request):
    if request.method == "POST":
        # data = json.loads(request.body)
        data = request.POST
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        phone_number = data.get("phone_no")
        password = data.get("password_1")
        confirm_password = data.get("password_2")
        address = data.get("address")
        dob = data.get("dob")
        height = data.get("height")
        weight = data.get("weight")
        blood_group = data.get("blood_group")
        gender = data.get("gender")
        medical_history = data.getlist("medical_history")

        if not (first_name and email and password and confirm_password and address and dob and phone_number and height and weight and gender and blood_group):
            res = {"message" : "Some field is missing"}
            return JsonResponse(res, status = 400)
        if last_name is None:
            last_name = ""
        if not bool(re.match(r'\b[a-z|A-Z]{2,25}', first_name)):
            res = {"message" : "First name is invalid"}
            return JsonResponse(res, status = 400)
        elif not (last_name == ""):
            if not bool(re.match(r"\b[a-z|A-Z]{2,25}", last_name)):
                res = {"message" : "Last name is invalid"}
                return JsonResponse(res, status = 400)
        elif not (bool(re.match(r"\d{2, 3}", height)) and bool(re.match(r"\d{2, 3}", weight))):
            res = {"message" : "Height or weight is invalid"}
            return JsonResponse(res, status = 400)
        elif len(address) == 0:
            res = {"message" : "Address is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", password)):
            res = {"message" : "Password is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"(0|91)?[6-9][0-9]{9}", phone_number)):
            res = {"message" : "Phone number is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"\bMale|Female", gender)):
            # print("hi")
            res = {"message" : "Gender is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"(A|B|AB|O)[+-]", blood_group)):
            res = {"message" : "Blood group is invalid", "hint" : "A+, AB+, etc."}
            return JsonResponse(res, status = 400)
        user_obj = CustomUser.objects.filter(email = email).values("email")
        if user_obj:
            res = {"message" : "E-mail is already registered"}
            return JsonResponse(res, status = 409)
        if password == confirm_password:
            d = dob.split("-")
            dob = datetime.date(int(d[0]), int(d[1]), int(d[2]))
            if medical_history == "None":
                medical_history = None
            else:
                if medical_history.count("None") != 0:
                    history = ','.join(medical_history)
                else:
                    res = {"message" : "Medical history is invalid"}
            user_obj = CustomUser.objects.create_patient(password = password, first_name = first_name, last_name = last_name, email = email, phone_number = phone_number)
            user_obj.patientinfo_set.create(height = height, weight = weight, dob = dob, blood_group = blood_group, gender = gender, address = address, medical_history = history)
            res = {"message" : "Patient registration is successful"}
            return JsonResponse(res, status = 201)
        else:
            res = {"message" : "Confirm password is not matching"}
            return JsonResponse(res, status = 400)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)