from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
import re
from users.models import CustomUser, LeftPanel
from django.conf import settings
from doctor.models import Speciality
from patient.models import Appointment,Prescription, AppointmentInfo
import datetime
from .functions import generate_pdf
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in



def index(request):
    res = {"message" : "doctor app index api"}
    return JsonResponse(res, status = 200)
    
def registration(request):
    if request.method == "POST":
        data = request.POST
        email = data.get("email")
        first_name = data.get("first_name")
        first_name = first_name.capitalize()
        last_name = data.get("last_name")
        last_name = last_name.capitalize()
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
            res = {'message' : "Information given is not sufficient"}
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
        user_query_set = CustomUser.objects.filter(email = email)
        if user_query_set:
            res = {"message" : "E-mail is already registered"}
            return JsonResponse(res, status = 409)
        if password == confirm_password:
            user_obj = CustomUser.objects.create_doctor(password = password, first_name = first_name, last_name = last_name, email = email, phone_number = phone_number)
            user_obj.doctorinfo_set.create(gender = gender, speciality = speciality_obj, address = address)
            if image:
                user_obj.profile_photo = image
                user_obj.save()
            res = {"message" : "Doctor registration is successful"}
            user = authenticate(email = email, password = password)
            l_in(request, user)
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
    if not request.user.role.role == "Doctor":
        res = {"message" : "Feature is only available for doctors only"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        appointment_query_set = Appointment.objects.filter(preferred_doctor = request.user)
        appointment_obj = ""
        if not appointment_query_set:
            res = {"message" : "There are no appointments for you to show"}
            return JsonResponse(res, status = 404)
        else:
            appointment_obj = appointment_query_set[0]
            appointment_info_query_set = appointment_obj.appointmentinfo_set.reverse()
            if appointment_info_query_set:
                flag = True
                for appointment_info in appointment_info_query_set:
                    appointment_info_obj = appointment_info
                    if appointment_info_obj.rejection_status == False and appointment_info_obj.receptionist_approval_status == False:
                        flag = False
                    else:
                        flag = True
                        break
                if not flag:
                    res = {"message" : "No action has been taken by the receptionist on the requested appointments"}
                    return JsonResponse(res, status = 400)
            else:
                res = {"message" : "Receptionist has not forwarded the appointment requests"}
                return JsonResponse(res, status = 202)
        res = {"message" : "success", "data" : {"scheduled_appointments" : [], "previous_appointments" : [], "requested_appointments" : []}}
        apntmnt_dict = {}
        for appointment in appointment_query_set:
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

            appointment_info_query_set = appointment.appointmentinfo_set.reverse()
            if not appointment_info_query_set:
                continue
            appointment_info_obj = appointment_info_query_set[0]
            if appointment_info_obj.receptionist_approval_status == True and appointment_info_obj.rejection_status == False and appointment_info_obj.doctor_approval_status == False and appointment_info_obj.payment_status == True:
                res["data"]["requested_appointments"].append(apntmnt_dict)
            if appointment_info_obj.doctor_approval_status == True and appointment_info_obj.prescription_status == False and appointment_info_obj.payment_status == True and appointment_info_obj.rejection_status == False:
                slot_start = appointment.slot_start.strftime("%H:%M:%S")
                apntmnt_dict["slot_start"] = slot_start
                slot_end = appointment.slot_end.strftime("%H:%M:%S")
                apntmnt_dict["slot_end"] = slot_end
                res["data"]["scheduled_appointments"].append(apntmnt_dict)
            if appointment_info_obj.payment_status == True and appointment_info_obj.rejection_status == False and appointment_info_obj.prescription_status == True:
                res["data"]["previous_appointments"].append(apntmnt_dict)
        return JsonResponse(res, status = 200)
    elif request.method == "PATCH":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        if not appointment_id:
            res = {"message" : "Appointment id is required"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id)
        if not appointment_query_set:
            res = {"message" : f"There is no such appointment with id : {appointment_id}"}
            return JsonResponse(res, status = 400)
        appointment_obj = appointment_query_set[0]
        appointment_info_query_set = appointment_obj.appointmentinfo_set.reverse()
        if appointment_info_query_set:
            appointment_info_obj = appointment_info_query_set[0]
            if appointment_info_obj.receptionist_approval_status == True and appointment_info_obj.prescription_status == False:
                appointment_info_obj.doctor_approval_status = True
                appointment_info_obj.last_modified_by_doctor = datetime.datetime.now()
                appointment_info_obj.save()
                res = {"message" : f"Appointment with id = {appointment_id} is scheduled on {appointment_obj.requested_for} for the slot : from {appointment_obj.slot_start.strftime("%H:%M:%S")} to {appointment_obj.slot_end.strftime("%H:%M:%S")}"}
                return JsonResponse(res, status = 200)
            else:
                res = {"message" : "This appointment has not been approved by the receptionist"}
                return JsonResponse(res, status = 400)
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
        appointment_query_set = Appointment.objects.filter(id = appointment_id)
        if not appointment_query_set:
            res = {"message" : f"There does not exist any appointment with appointment_id : {appointment_id}"}
            return JsonResponse(res, status = 404)
        appointment_obj = appointment_query_set[0]
        appointment_info_query_set = appointment_obj.appointmentinfo_set.values() #filter(receptionist_approval_status = True, doctor_approval_status = False, prescription_status = False)
        if not appointment_info_query_set:
            res = {"message" : "The appointment has not been seen by the receptionist"}
            return JsonResponse(res, status = 400)
        else:
            appointment_info_obj = appointment_info_query_set[0]
            if appointment_info_obj.receptionist_approval_status == True:
                if appointment_info_obj.doctor_approval_status == False:
                    appointment_info_obj.rejection_status = True
                    appointment_info_obj.remark = remark
                    res = {"message" : "The appointment is successfully rejected"}
                    return JsonResponse(res, status = 200)
                else:
                    res = {"message" : f"The appointment is scheduled on {appointment_obj.requested_for} from {appointment_obj.slot_start} to {appointment_obj.slot_end}"}
                    return JsonResponse(res, status = 409)
            else:
                res = {"message" : "The appointment is not approved by receptionist"}
                return JsonResponse(res, status = 400)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def give_prescription(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.role.role == "Doctor":
        res = {"message" : "Feature only available to doctors only"}
        return JsonResponse(res, status = 403)
    if request.method == "POST":
        data = request.POST
        appointment_id = data.get("appointment_id")
        appointment_obj = Appointment.objects.filter(id = appointment_id)[0]
        medicine_list = data.getlist("medicine")
        frequency_list = data.getlist("frequency")
        number_of_days_list = data.getlist("number_of_days")
        if not (medicine_list and frequency_list and number_of_days_list):
            res = {"message" : "Information given is not sufficient"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id)
        if not appointment_query_set:
            res = {"message" : f"There is no appointment with appointment_id : {appointment_id}"}
            return JsonResponse(res, status = 400)
        appointment_obj = appointment_query_set[0]
        appointment_info_query_set = appointment_obj.appointmentinfo_set.reverse()
        print(appointment_info_query_set)
        if not appointment_info_query_set:
            res = {"message" : "The appointment has not been seen by the receptionist"}
            return JsonResponse(res, status = 400)
        appointment_info_obj = appointment_info_query_set[0]
        if not appointment_info_obj.rejection_status == False:
            res = {"message" : "The appointment is already rejected by the receptionist"}
            return JsonResponse(res, status = 409)
        if appointment_info_obj.doctor_approval_status == True:
            if appointment_info_obj.prescription_status == True:
                res = {"message" : "The prescription for this appointment is already generated"}
                return JsonResponse(res, status = 409)
            else:
                appointment_info_obj.prescription_status = True
                for i in range(len(medicine_list)):
                    medicine = medicine_list[i]
                    if not medicine:
                        res = {"message" : "Invalid medicine name"}
                        return JsonResponse(res, status = 400)
                    frequency = frequency_list[i]
                    if not frequency:
                        res = {"message" : "Frequency can not be empty"}
                        return JsonResponse(res, status = 400)
                    else:
                        if int(frequency) > 4:
                            res = {"message" : "Frequency cannot be greater than 4"}
                            return JsonResponse(res, status = 400)
                    number_of_days = number_of_days_list[i]
                    if int(number_of_days) > 365:
                        res = {"message" : "Medicine can be given for one year at max"}
                        return JsonResponse(res, status = 400)
                    prescription_obj = Prescription.objects.create(medicine = medicine, frequency = frequency, number_of_days = number_of_days)
                    prescription_obj.appointment.add(appointment_obj)
                appointment_info_obj.save()
                res = {"message" : "Prescription is generated succesfully"}
                return JsonResponse(res, status = 201)
        else:
            res = {"message" : "The appointment is not been approved by you"}
            return JsonResponse(res, status = 400)

def profile(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.role.role == "Doctor":
        res = {"message" : "Only doctor can see his/her profile"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        profile_query_set = CustomUser.objects.filter(id = request.user.id).values("id", "first_name", "last_name", "email", "phone_number")
        res = {"message" : "success", "data" : [], "more_info" : []}
        res["data"].append((profile_query_set)[0])
        info_set = request.user.doctorinfo_set.values("gender", "address", "profile_photo")
        speciality = request.user.doctorinfo_set.reverse()[0].speciality.speciality
        more_info = info_set[0]
        more_info["speciality"] = speciality
        print(more_info)
        res["more_info"].append(more_info)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid requet method"}
        return JsonResponse(res, status = 405)