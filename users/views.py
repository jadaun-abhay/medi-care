from django.shortcuts import render

# Create your views here.

import json
from users.models import CustomUser
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out

def index(request):
    if request.method == "GET":
        res = {"message" : "User app index A.P.I."}
        return JsonResponse(res, status = 200)
    
def login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        user_obj = CustomUser.objects.filter(email = email).values("is_doctor", "is_patient")
        if user_obj is None:
            res = {"message" : "User is not registered"}
            return JsonResponse(res, status = 401)
        is_doctor = user_obj[0].get("is_doctor")
        is_patient = user_obj[0].get("is_patient")
        if is_patient:
            status = "Patient"
        elif is_doctor:
            status = "Doctor"
        else:
            status = "Receptionist"
        user = authenticate(email = email, password = password)
        if user:
            l_in(request, user)
            res = {"message" : "Login is successfull", "status" : status}
            return JsonResponse(res, status = 200)
        else:
            res = {"message" : "Incorrect password"}
            return JsonResponse(res, status = 401)
    elif request.method == 'GET':
        if request.user.is_authenticated:
            res = {"message" : "Login is successful"}
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
