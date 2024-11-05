from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
from users.models import CustomUser, Roles
import re
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out
import datetime
from django.conf import settings
from .models import Prescription, Appointment
from doctor.models import PaymentDetails
from django.http import QueryDict

def index(request):
    res = {"message" : "patient app index api"}
    return JsonResponse(res, status = 200)

def registration(request):
    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name")
        first_name = first_name.capitalize()
        last_name = data.get("last_name")
        last_name = last_name.capitalize()
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
        if image:
            extension = image.name.split(".")[-1]
            extension = extension.lower()
            content_type = image.content_type
            if extension not in settings.WHITELISTED_IMAGE_TYPES.keys():
                res = {"message" : "Invalid image extension"}
                return JsonResponse(res, status = 400)
            elif content_type not in settings.WHITELISTED_IMAGE_TYPES.values():
                res = {"message" : "Invalid image content type"}
                return JsonResponse(res, status = 400)
        if not (first_name and email and password and confirm_password and address and dob and phone_number and height and weight and gender and blood_group):
            res = {"message" : "Information given is not sufficient"}
            return JsonResponse(res, status = 400)
        try:
            res = bool(datetime.datetime.strptime(dob, "%d-%m-%Y"))
        except ValueError:
            res = {"message" : "format of date of birth is invalid.required format : \'dd-mm-yyyy\'"}
            return JsonResponse(res, status = 400)
        if not bool(re.match(r'\b[a-z|A-Z]{2,25}', first_name)):
            res = {"message" : "First name is invalid"}
            return JsonResponse(res, status = 400)
        elif last_name:
            if not bool(re.match(r"\b[a-z|A-Z]{2,25}", last_name)):
                res = {"message" : "Last name is invalid"}
                return JsonResponse(res, status = 400)
        elif not (30 <= height <= 251) and (2 <= weight <= 727):
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
        user_query_set= CustomUser.objects.filter(email = email)
        if user_query_set:
            res = {"message" : "E-mail is already registered"}
            return JsonResponse(res, status = 409)
        elif password == confirm_password:
            d = dob.split("-")
            dob = datetime.date(int(d[0]), int(d[1]), int(d[2]))
            if medical_history == ["None"]:
                medical_history = None
            else:
                if len(medical_history) > 1 and medical_history.count("None") > 0:
                    res = {"message" : "Medical history is invalid"}
                    return JsonResponse(res, status = 400)
            user_obj = CustomUser.objects.create_patient(password = password, first_name = first_name, last_name = last_name, email = email, phone_number = phone_number)
            user_obj.patientinfo_set.create(height = height, weight = weight, dob = dob, blood_group = blood_group, gender = gender, address = address, medical_history = medical_history)
            if image:
                user_obj.profile_photo = image
                user_obj.save()
            res = {"message" : "Patient registration is successful"}
            user = authenticate(email = email, password = password)
            l_in(request, user)
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
    if request.user.role.role != "Patient":
        res = {"message" : "This page is for patient"}
        return JsonResponse(res, status = 403)
    if request.method == "POST":
        data = json.loads(request.body)
        preferred_doctor_id = data.get("preferred_doctor_id")
        applied_for = data.get("date")
        problem_description = data.get("problem_description")
        symptoms = data.get("symptoms")
        slot_start = data.get("from")
        slot_end = data.get("to")
        if not (preferred_doctor_id and applied_for and problem_description and symptoms and slot_start and slot_end):
            res = {"message" : "Information given is not sufficient"}
            return JsonResponse(res, status = 400)
        if not preferred_doctor_id.isnumeric():
            res = {"message" : "Doctor id must be numeric"}
            return JsonResponse(res, status = 400)
        try:
            res = bool(datetime.datetime.strptime(applied_for, "%d-%m-%Y"))
        except ValueError:
            res = {"message" : "format for requested_date is invalid. Request format : \'dd-mm-yyyy\'"}
            return JsonResponse(res, status = 400)
        try:
            res = bool(datetime.datetime.strptime(slot_start, '%H:%M:%S'))
        except ValueError:
            res = {"message" : "format of slot-start is invalid\nRequired format : \'hh-mm-ss\' (24-hour format)"}
            return JsonResponse(res, status = 400)
        try:
            res = bool(datetime.datetime.strptime(slot_end, '%H:%M:%S'))
        except ValueError:
            res = {"message" : "format of slot-end is invalid\nRequired format : \'hh-mm-ss\' (24-hour format)"}
            return JsonResponse(res, status = 400)
        slot_start = slot_start.split(":")
        slot_start = datetime.time(int(slot_start[0]), int(slot_start[1]), int(slot_start[2]))
        slot_end = slot_end.split(":")
        slot_end = datetime.time(int(slot_end[0]), int(slot_end[1]), int(slot_end[2]))
        applied_for = applied_for.split("-")
        applied_for = datetime.date(int(applied_for[2]), int(applied_for[1]), int(applied_for[0]))
        start_datetime_str = applied_for.strftime("%Y-%m-%d") + " " + slot_start.strftime("%H:%M:%S")
        end_datetime_str = applied_for.strftime("%Y-%m-%d") + " " + slot_end.strftime("%H:%M:%S")
        slot_start_datetime = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
        slot_end_datetime = datetime.datetime(end_datetime_str, "%Y-%m-%d %H:%M:%S")
        diff = ""
        if slot_start < slot_end:
            diff = slot_end_datetime - slot_start_datetime
            hours_diff = (diff.seconds)/3600
            if hours_diff > 2:
                res = {"message" : "Appointment can be booked for 2 hours max"}
                return JsonResponse(res, status = 400)
        else:
            res = {"message" : "invalid slot requested"}
            return JsonResponse(res, status = 400)
        preferred_doctor_query_set = CustomUser.objects.filter(id = preferred_doctor_id, role_id = 1)
        preferred_doctor_obj = ""
        if not preferred_doctor_query_set:
            res = {"message" : "There does not exist any doctor with such id"}
            return JsonResponse(res, status = 400)
        else:
            preferred_doctor_obj = preferred_doctor_query_set[0]
        if not applied_for > datetime.date.today():
            res = {"message" : "Request date must not be in past"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(preferred_doctor = preferred_doctor_obj, requested_for = applied_for)
        if appointment_query_set:
            for appointment in appointment_query_set:
                if appointment.patient == request.user and (appointment.slot_start < slot_start < appointment.slot_end or appointment.slot_start < slot_end < appointment.slot_end):
                    res = {"message" : "There already exists an appointment applied by you at the same slot"}
                    return JsonResponse(res, status = 400)
                appointment_info_query_set = appointment.appointmentinfo_set.reverse().filter(doctor_approval_status = True)
                if appointment_info_query_set:
                    if appointment.slot_start < slot_start < appointment.slot_end or appointment.slot_start < slot_end < appointment.slot_end:
                        res = {"message" : "Doctor is busy at the requested slot, try booking another slot"}
                        return JsonResponse(res, status = 400)
        request.user.appointment_set.create(preferred_doctor = preferred_doctor_obj, problem_description = problem_description, symptoms = symptoms, requested_for = applied_for, slot_start = slot_start, slot_end = slot_end)
        res = {"message" : "success", "data" : "Appointment has been booked succesfully"}
        return JsonResponse(res, status = 201)
    elif request.method == "GET":
        appointment_query_set = request.user.appointment_set.all()
        if not appointment_query_set:
            res = {"message" : "You haven't booked any appointments to show"}
            return JsonResponse(res, status = 202)
        res = {"message" : "success", "data" : {"pending_appointments" : [], "scheduled_appointments" : [], "rejected_appointments" : [], "pending_payments" : [], "success_appointments" : []}}
        # print(appointment_query_set.values())
        for appointment in appointment_query_set:
            my_dict = {}
            appointment_id = appointment.id
            my_dict["appointment_id"] = appointment_id
            problem_description = appointment.problem_description
            my_dict["problem_description"] = problem_description
            requested_at = appointment.requested_at.strftime("%d/%b/%Y at %H:%M:%S")
            my_dict["requested_at"] = requested_at
            requested_for = appointment.requested_for.strftime("%d/%b/%Y")
            my_dict["requested_for"] = requested_for
            slot_start = appointment.slot_start.strftime("%H:%M:%S")
            my_dict["slot_start"] = slot_start
            slot_end = appointment.slot_end.strftime("%H:%M:%S")
            my_dict["slot_end"] = slot_end
            speciality = appointment.preferred_doctor.doctorinfo_set.reverse()[0].speciality.speciality
            my_dict["doctor_speciality"] = speciality
            preferred_doctor_name = appointment.preferred_doctor.first_name
            if appointment.preferred_doctor.last_name:
                preferred_doctor_name += " " + appointment.preferred_doctor.last_name
            my_dict["preferred_doctor_name"] = preferred_doctor_name

            appointment_info_query_set = appointment.appointmentinfo_set.reverse()
            if not appointment_info_query_set:
                res["data"]["pending_appointments"].append(my_dict)
            else:
                appointment_info_obj = appointment_info_query_set[0]
                if appointment_info_obj.rejection_status == False and appointment_info_obj.doctor_approval_status == False and appointment_info_obj.receptionist_approval_status == False:
                    res["data"]["pending_appointments"].append(my_dict)
                if appointment_info_obj.doctor_approval_status == True and appointment_info_obj.payment_status == True and appointment_info_obj.prescription_status == False:
                    res["data"]["scheduled_appointments"].append(my_dict)
                if appointment_info_obj.rejection_status == True:
                    my_dict["remark"] = appointment_info_obj.remark
                    res["data"]["rejected_appointments"].append(my_dict)
                if appointment_info_obj.rejection_status == False and appointment_info_obj.payment_status == False:
                    res["data"]["pending_payments"].append(my_dict)
                if appointment_info_obj.payment_status == True and appointment_info_obj.prescription_status == True:
                    # payment = PaymentDetails.objects.filter(appointment = appointment_obj)
                    # payment_obj = payment[0]
                    my_dict["payment_id"] = 7 # payment_obj.id
                    my_dict["amount"] = 5000000 # payment_obj.amount
                    res["data"]["success_appointments"].append(my_dict)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)
    
def get_prescription(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required !!!"}
        return JsonResponse(res, status = 401)
    if not request.user.role.role == "Patient":
        res = {"message" : "Feature is only available to the patient"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        appointment_id = request.GET.get("appointment_id")
        if not appointment_id:
            res = {"message" : "Information provided is not suffiecient"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id)
        if not appointment_query_set:
            res = {"message" : f"There does not exist any appointment with appointment_id : {appointment_id}"}
            return JsonResponse(res, status = 404)
        appointment_obj = appointment_query_set[0]
        appointment_info_query_set = appointment_obj.appointmentinfo_set.reverse()
        if not appointment_info_query_set:
            res = {"message" : "No action has been taken on your requested appointment"}
            return JsonResponse(res, status = 400)
        appointment_info_obj = appointment_info_query_set[0]
        if not appointment_info_obj.prescription_status:
            res = {"message" : "The prescription is not generated yet"}
            return JsonResponse(res, status = 204)
        if not appointment_info_obj.payment_status:
            res = {"message" : "Payment is required to get the prescription"}
            return JsonResponse(res, status = 402)
        prescription_query_set = appointment_obj.prescription_set.all().values()
        res =  {"message" : "success", "data" : []}
        for med_info in prescription_query_set:
            res["data"].append(med_info)
        return JsonResponse(res, status = 200)
    
def profile(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required"}
        return JsonResponse(res, status = 401)
    if not request.user.role.role == "Patient":
        res = {"message" : "Only patient can see his/her profile"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        profile_query_set = CustomUser.objects.filter(id = request.user.id).values("id", "first_name", "last_name", "email", "phone_number", "profile_photo")
        res = {"message" : "success", "data" : [], "more_info" : []}
        res["data"].append(profile_query_set[0])
        info_query_set = request.user.patientinfo_set.values("gender", "dob", "blood_group", "address", "height", "weight", "medical_history")
        res["more_info"].append(info_query_set[0])
        return JsonResponse(res, status = 200)
    elif request.method == "POST":
        data = request.POST
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_no")
        gender = data.get("gender")
        height = data.get("height")
        weight = data.get("weight")
        date_of_birth = data.get("dob")
        blood_group = data.get("blood_group")
        address = data.get("address")
        medical_history = data.get("medical_history")
        image = request.FILES.get("profile_image")
        print("image", image)
        if first_name:
            if not bool(re.match(r'\b[a-z|A-Z]{2,25}', first_name)):
                res = {"message" : "First name is invalid"}
                return JsonResponse(res, status = 400)
            request.user.first_name = first_name
            request.user.save()
        if last_name:
            if not bool(re.match(r"\b[a-z|A-Z]{2,25}", last_name)):
                res = {"message" : "Last name is invalid"}
                return JsonResponse(res, status = 400)
            request.user.last_name = last_name
            request.user.save()
        if phone_number:
            if not bool(re.match(r"(0|91)?[6-9][0-9]{9}", phone_number)):
                res = {"message" : "Invalid phone number"}
                return JsonResponse(res, status = 400)
            request.user.phone_number = phone_number
            request.user.save()
        if image:
            extension = image.name.split(".")[-1]
            extension = extension.lower()
            if extension not in settings.WHITELISTED_IMAGE_TYPES.keys():
                res = {"message" : "Invalid image extension"}
                return JsonResponse(res, status = 400)
            content_type = image.content_type
            if content_type not in settings.WHITELISTED_IMAGE_TYPES.values():
                res = {"message" : "Invalid image content type"}
                return JsonResponse(res, status = 400)
            image_name = image.name
            print(image_name)
            request.user.profile_photo = image
            request.user.save()
        if gender:
            if not bool(re.match(r"\bmale|female", gender)):
                res = {"message" : "Gender is invalid"}
                return JsonResponse(res, status = 400)
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.gender = gender
            patient_info_obj.save()
        if height:
            if not (30 <= height <= 251):
                res = {"message" : "Height is invalid"}
                return JsonResponse(res, status = 400)
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.height = height
            patient_info_obj.save()
        if weight:
            if not (2 <= weight <= 727):
                res = {"message" : "Weight is invalid"}
                return JsonResponse(res, status = 400)
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.weight = weight
            patient_info_obj.save()
        if date_of_birth:
            if not bool(re.match("\d\d[-]\d\d[-]\d\d\d\d"), date_of_birth):
                res = {"message" : "date of birth is invalid"}
                return JsonResponse(res, status = 400)
            d = date_of_birth.split("-")
            date_of_birth = datetime.date(int(d[0]), int(d[1]), int(d[2]))
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.dob = date_of_birth
            patient_info_obj.save()
        if blood_group:
            if not bool(re.match(r"(A|B|AB|O)[+-]", blood_group)):
                res = {"message" : "Blood group is invalid", "hint" : "A+, AB+, etc."}
                return JsonResponse(res, status = 400)
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.blood_group = blood_group
            patient_info_obj.save()
        if address:
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.address = address
            patient_info_obj.save()
        if medical_history:
            patient_info_obj = request.user.patient_info.reverse()[0]
            patient_info_obj.medical_history = medical_history
            patient_info_obj.save()
        res = {"message" : "Updations are applied successfully"}
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)