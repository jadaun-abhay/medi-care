from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
from users.models import CustomUser, LeftPanel
import re
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out
import datetime
from django.conf import settings

def index(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        panel_obj = LeftPanel.objects.filter(for_patient = True).values("title", "state", "priority", "icon")
        res = {"message" : "success", "data" : {"title" : "PATIENT", "children" : []}}
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

def registration(request):
    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        phone_number = data.get("phone_no")
        password = data.get("password_1")
        confirm_password = data.get("password_2")
        address = data.get("address")
        dob = data.get("dob")
        height = int(data.get("height"))
        weight = int(data.get("weight"))
        blood_group = data.get("blood_group")
        gender = data.get("gender")
        medical_history = data.getlist("medical_history")
        image = request.FILES.get("profile_image")
        if not image is None:
            extension = image.name.split(".")[-1]
            extension = extension.lower()
            if extension not in settings.WHITELISTED_IMAGE_TYPES.keys():
                res = {"message" : "Invalid image extension"}
                return JsonResponse(res, status = 400)
            content_type = image.content_type
            if content_type not in settings.WHITELISTED_IMAGE_TYPES.values():
                res = {"message" : "Invalid image content type"}
                return JsonResponse(res, status = 400)
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
        elif not (55 <= height <= 251) and (48 <= weight <= 727):
            res = {"message" : "Height or weight is invalid"}
            return JsonResponse(res, status = 400)
        elif len(address) == 0:
            res = {"message" : "Address is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", password)):
            res = {"message" : "Password is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"(0|91)?[6-9][0-9]{9}", phone_number)):
            res = {"message" : "Phone number is invalid"}
            return JsonResponse(res, status = 400)
        elif not bool(re.match(r"\bmale|female", gender)):
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
            if medical_history == ["None"]:
                medical_history = None
            else:
                if len(medical_history) > 1 and medical_history.count("None") > 0:
                    res = {"message" : "Medical history is invalid"}
                    return JsonResponse(res, status = 400)
            user_obj = CustomUser.objects.create_patient(password = password, first_name = first_name, last_name = last_name, email = email, phone_number = phone_number)
            if image is None:
                user_obj.patientinfo_set.create(height = height, weight = weight, dob = dob, blood_group = blood_group, gender = gender, address = address, medical_history = medical_history)
            else:
                user_obj.patientinfo_set.create(height = height, weight = weight, dob = dob, blood_group = blood_group, gender = gender, address = address, medical_history = medical_history, profile_photo = image)
            # user = authenticate(email = email, password = password)
            # l_in(request, user)
            res = {"message" : "Patient registration is successful"}
            return JsonResponse(res, status = 201)
        else:
            res = {"message" : "Confirm password is not matching"}
            return JsonResponse(res, status = 400)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)

def appointment(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.is_patient:
        res = {"message" : "Only patient can initiate an appointment"}
        return JsonResponse(res, status = 403)
    if request.method == "POST":
        data = json.loads(request.body)
        preferred_doctor = data.get("preferred_doctor_id")
        preferred_doctor_obj = CustomUser.objects.filter(id = preferred_doctor, is_doctor = True)
        if not preferred_doctor_obj:
            res = {"message" : "Doctor is not known to us"}
            return JsonResponse(res, status = 400)
        preferred_doctor_obj = preferred_doctor_obj[0]
        applied_for = data.get("applied_for")
        date_time_list = applied_for.split(", ")
        date = date_time_list[0]
        time = date_time_list[1]
        date = date.split("/")
        time = time.split(":")
        applied_for = datetime.datetime(int(date[2]), int(date[1]), int(date[0]), int(time[0]), int(time[1]), int(time[2]))
        problem_description = data.get("problem_description")
        symptoms = data.get("symptoms")
        if not (preferred_doctor and applied_for and problem_description and symptoms):
            res = {"messsage" : "Some fields are missing"}
            return JsonResponse(res, status = 400)
        new_appointment_status = False
        booked_appointment_date = ""
        booked_appointment_time_hour = -1
        applied_for_date = ""
        applied_for_time_hour = -1
        appointment_obj = request.user.appointment_set.filter(rejection_status = False, prescription_status = False, requested_for = applied_for)
        if appointment_obj:
            res = {"message" : f"Your appointment is already booked on {appointment_obj[0].requested_for.strftime("%d/%b/%Y at %H:%M:%S")}", "data" : {"appointment_id" : appointment_obj[0].id}}
            return JsonResponse(res, status = 400)
        else:
            if appointment_obj:
                booked_appointment_date = appointment_obj[0].requested_for.date()
                booked_appointment_time_hour = appointment_obj[0].requested_for.time().strftime("%H")
                applied_for_date = applied_for.date()
                applied_for_time_hour = applied_for.time().strftime("%H")
            else:
                new_appointment_status = True
        if (booked_appointment_date == applied_for_date and (applied_for_time_hour == str(int(booked_appointment_time_hour+1)) or applied_for_time_hour == str(int(booked_appointment_time_hour-1)))) or new_appointment_status:
            request.user.appointment_set.create(preferred_doctor = preferred_doctor_obj, problem_description = problem_description, symptoms = symptoms, requested_for = applied_for)
            res = {"message" : "success", "data" : "Appointment has been booked succesfully"}
            return JsonResponse(res, status = 201)
        else:
            res = {"message" : "Doctor is not available at the requested time. Try requesting for 1 hour before or after. Otherwise try for another date"}
            return JsonResponse(res, status = 400)
    elif request.method == "GET":
        appointment_query_set = request.user.appointment_set.all()
        if not appointment_query_set:
            res = {"message" : "You haven't booked any appointments to show"}
            return JsonResponse(res, status = 202)
        res = {"message" : "success", "data" : {"pending_appointments" : [], "scheduled_appointments" : [], "rejected_appointments" : [], "payment_appointments" : [], "success_appointments" : []}}
        # print(appointment_query_set.values())
        for appointment in appointment_query_set:
            my_dict = {}
            appointment_id = appointment.id
            my_dict["appointment_id"] = appointment_id
            problem_description = appointment.problem_description
            my_dict["problem_description"] = problem_description
            requested_at = appointment.requested_at.strftime("%d/%b/%Y at %H:%M:%S")
            my_dict["requested_at"] = requested_at
            requested_for = appointment.requested_for.strftime("%d/%b/%Y at %H:%M:%S")
            my_dict["requested_for"] = requested_for
            preferred_doctor = appointment.preferred_doctor
            my_dict["preferred_doctor_id"] = preferred_doctor.id
            speciality = appointment.preferred_doctor.doctorinfo_set.reverse()[0].speciality.speciality
            my_dict["speciality"] = speciality
            preferred_doctor_name = appointment.preferred_doctor.first_name
            if appointment.preferred_doctor.last_name:
                preferred_doctor_name += " " + appointment.preferred_doctor.last_name
            my_dict["preferred_doctor_name"] = preferred_doctor_name

            if appointment.rejection_status == False and appointment.cure_status == False:
                res["data"]["pending_appointments"].append(my_dict)
            if appointment.cure_status == True:
                res["data"]["scheduled_appointments"].append(my_dict)
            if appointment.rejection_status == True:
                my_dict["remark"] = appointment.remark
                res["data"]["rejected_appointments"].append(my_dict)
            if appointment.prescription_status == True:
                # Will be added
                res["data"]["payment_appointments"].append(my_dict)
            if appointment.payment == True:
                res["data"]["success_appointments"].append(my_dict)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
