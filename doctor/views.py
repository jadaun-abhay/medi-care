from django.shortcuts import render

# Create your views here.


import json
from django.http import JsonResponse
import re
from users.models import CustomUser
from django.conf import settings
from doctor.models import Speciality



def index(request):
    if request.method == "GET":
        res = {"message" : "doctor app index A.P.I"}
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def registration(request):
    if request.method == "POST":
        data = request.POST
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_no")
        password = data.get("password_1")
        confirm_password = data.get("password_2")
        gender = data.get("gender")
        speciality_id = data.get("speciality_id")
        address = data.get("address")
        image = request.FILES.get("profile_image")
        extension = image.name.split(".")[-1]
        extension = extension.lower()
        if extension not in settings.WHITELISTED_IMAGE_TYPES.keys():
            res = {"message" : "Invalid image extension"}
            return JsonResponse(res, status = 400)
        content_type = image.content_type
        if content_type not in settings.WHITELISTED_IMAGE_TYPES.values():
            res = {"message" : "Invalid image content type"}
            return JsonResponse(res, status = 400)
        if not (email and first_name and phone_number and password and confirm_password and gender and speciality_id and address):
            res = {'message' : "Some field is missing"}
            return JsonResponse(res, status = 400)
        if last_name is None:
            last_name = ""
        if not bool(re.match(r'\b[a-zA-Z]+[a-z]{1,25}', first_name)):
            res = {"message" : "First name is invalid"}
            return JsonResponse(res, status = 400)
        elif not (last_name == ""):
            if not bool(re.match(r'\b[a-zA-Z]+[a-z]{1,25}', last_name)):
                res = {"message" : "Last name is invalid"}
                return JsonResponse(res, status = 400)
        elif len(address) == 0:
            res = {"message" : "Address is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"(0|91)?[6-9][0-9]{9}", phone_number)):
            res = {"message" : "Phone number is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", password)):
            res = {"message" : "Password is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"\bmale|female", gender)):
            res = {"message" : "Gender is invalid"}
            return JsonResponse(res, status = 400)
        speciality_obj = Speciality.objects.filter(id = speciality_id)[0]
        if speciality_obj is None:
            res = {"message" : "Speciality is not known"}
            return JsonResponse(res, status = 400)
        user_obj = CustomUser.objects.filter(email = email).values("email")
        if user_obj:
            res = {"message" : "E-mail is already registered"}
            return JsonResponse(res, status = 409)
        if password == confirm_password:
            user_obj = CustomUser.objects.create_doctor(password = password, first_name = first_name, last_name = last_name, email = email, phone_number = phone_number)
            if image is None:
                user_obj.doctorinfo_set.create(gender = gender, speciality = speciality_obj, address = address)
            else:
                user_obj.doctorinfo_set.create(gender = gender, speciality = speciality_obj, address = address, profile_photo = image)
            res = {"message" : "Doctor registration is successful"}
            return JsonResponse(res, status = 201)
        else:
            res = {"message" : "Confirm password is not matching"}
            return JsonResponse(res, status = 400)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
        