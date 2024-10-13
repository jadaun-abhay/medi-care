from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
import re
from users.models import CustomUser, LeftPanel
from django.conf import settings
from doctor.models import Speciality
from patient.models import Appointment,Prescription
import datetime



def index(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        panel_obj = LeftPanel.objects.filter(for_doctor = True).values("title", "state", "priority", "icon")
        res = {"message" : "success", "data" : {"title" : "DOCTOR", "children" : []}}
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
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_no")
        password = data.get("password_1")
        confirm_password = data.get("password_2")
        gender = data.get("gender")
        speciality_id = data.get("speciality")
        address = data.get("address")
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
    
def appointments(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.is_doctor:
        res = {"message" : "Feature is only available for doctors only"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        appointment_obj = Appointment.objects.filter(preferred_doctor = request.user, rejection_status = False, prescription_status = False)
        if appointment_obj is None:
            res = {"message" : "There are no appointments for you"}
            return JsonResponse(res, status = 202)
        res = {"message" : "success", "data" : {"scheduled_appointments" : [], "previous_appointments" : [], "requested_appointments" : []}}
        apntmnt_dict = {}
        for appointment in appointment_obj:
            apntmnt_dict = {}
            appointment_id = appointment.id
            apntmnt_dict["appointment_id"] = appointment_id
            patient_id = appointment.patient.id
            apntmnt_dict["patient_id"] = patient_id
            patient_name = appointment.patient.first_name
            if appointment.patient.last_name:
                patient_name += " " + appointment.patient.last_name
            apntmnt_dict["patient_name"] = patient_name
            date_of_application = appointment.requested_at
            apntmnt_dict["initiated_at"] = date_of_application
            requested_for = appointment.requested_for
            apntmnt_dict["requested_for"] = requested_for
            problem_description = appointment.problem_description
            apntmnt_dict["problem_description"] = problem_description
            symptoms = appointment.symptoms
            apntmnt_dict["symptoms"] = symptoms
            if appointment.approval_status == True and appointment.rejection_status == False and appointment.cure_status == False:
                res["data"]["requested_appointments"].append(apntmnt_dict)
            if appointment.cure_status == True and appointment.prescription_status == False:
                res["data"]["scheduled_appointments"].append(apntmnt_dict)
            if appointment.payment == True:
                res["data"]["previous_appointments"].append(apntmnt_dict)
        return JsonResponse(res, status = 200)
    elif request.method == "PATCH":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        if not appointment_id:
            res = {"message" : "Appointment id is required"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id, approval_status = True, prescription_status = False)
        if not appointment_query_set:
            res = {"message" : f"There is no such appointment with id : {appointment_id}"}
            return JsonResponse(res, status = 400)
        appointment_query_set.update(cure_status = True, last_modified_by_doctor = datetime.datetime.now())
        res = {"message" : f"Appointment with id = {appointment_id} is scheduled on {appointment_query_set[0].requested_for}"}
        return JsonResponse(res, status = 200)
    elif request.method == "DELETE":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        remark = data.get("remark")
        if not remark:
            res = {"message" : "Remark is required"}
            return JsonResponse(res, status = 400)
        if not appointment_id:
            res = {"message" : "Appointment_id is required"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id, approval_status = True, cure_status = False, prescription_status = False)
        if not appointment_query_set:
            res = {"message" : f"There does not exist any appointment with appointment_id : {appointment_id}"}
            return JsonResponse(res, status = 404)
        appointment_obj = appointment_query_set[0]
        if appointment_obj.cure_status:
            res = {"message" : "The appointment is already scheduled"}
            return JsonResponse(res, 400)
        else:
            appointment_query_set.update(remark = remark, last_modified_by_doctor = datetime.datetime.now(), rejection_status = True)
            res = {"message" : f"Appointment with appointment id = {appointment_id} has been rejected"}
            return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def prescription(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.is_doctor:
        res = {"message" : "Feature only available to doctors only"}
        return JsonResponse(res, status = 403)
    if request.method == "POST":
        data = request.POST
        appointment_id = data.get("appointment_id")
        # appointment_obj = Appointment.objects.filter(id = appointment_id)[0]
        medicine_list = data.getlist("medicine")
        frequency_list = data.getlist("freq")
        number_of_days_list = data.getlist("qty")
        print(medicine_list)
        print(frequency_list)
        print(number_of_days_list)
        # for i in range(len(medicine_list)):
        #     medicine = medicine_list[i]
        #     frequency = frequency_list[i]
        #     number_of_days = number_of_days_list[i]
        #     prescription_obj = Prescription.objects.create(medicine = medicine, frequency = frequency, number_of_days = number_of_days)
        #     prescription_obj.appointment.add(appointment_obj)
        # res = {"message" : "Prescription is generated successfully"}
        # return JsonResponse(res, status = 201)


        

        