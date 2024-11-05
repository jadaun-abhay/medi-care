from django.shortcuts import render

# Create your views here.

import json
from users.models import CustomUser, Roles
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as l_in
from django.contrib.auth import logout as l_out
from doctor.models import DoctorInfo, Speciality
from patient.models import Appointment, AppointmentInfo
import datetime
from .models import LeftPanel
from .functions import send_payment_request_mail

def index(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            res = {"message" : "Login is required !!!"}
            return JsonResponse(res, status = 401)
        user_role = request.user.role
        left_panel_query_set = LeftPanel.objects.filter(role = user_role).values("title", "state", "priority", "icon")
        print(left_panel_query_set)
        if not left_panel_query_set:
            res = {"message" : "Requested role is not known"}
            return JsonResponse(res, status = 400)
        left_panel_obj = left_panel_query_set[0]
        # panel_obj = LeftPanel.objects.all().values("title", "state", "priority", "icon")
        res = {"message" : "success", "data" : {"title" : user_role.role , "children" : []}}
        for option in left_panel_query_set:
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
        if not (email and password):
            res = {"message" : "Information given is not sufficient"}
            return JsonResponse(res, status = 400)
        user_query_set = CustomUser.objects.filter(email = email)
        if not user_query_set:
            res = {"message" : "Email is not registered"}
            return JsonResponse(res, status = 401)
        user_obj = user_query_set[0]
        role_state = user_obj.role.state
        user = authenticate(email = email, password = password)
        if user:
            l_in(request, user)
            res = {"message" : "Login is successfull", "data" : {"state" : role_state}}
            return JsonResponse(res, status = 200)
        else:
            res = {"message" : "Incorrect password"}
            return JsonResponse(res, status = 401)
    elif request.method == 'GET':
        if request.user.is_authenticated:
            role_obj = request.user.role
            state = role_obj.state
            name = request.user.first_name
            last_name = request.user.last_name
            if last_name:
                name +=  " " + last_name
            profile_image = request.user.profile_photo.name
            res = {"message" : "Login is successfull", "data" : {"state" : state}, "profile_data" : {"name" : name, "photo" : profile_image}}
            return JsonResponse(res, status = 200)
        else:
            res = {"message" : "Login is required !!!"}
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
        if not request.user.role.role != "Receptionist":
            res = {'message' : "Feature is only available for the Receptionist"}
            return JsonResponse(res, status = 403)
        data = request.POST
        speciality = data.get("speciality")
        study = data.get("study")
        related_image = request.FILES.get("image")
        description = data.get("description")
        if not (speciality and study and related_image and description):
            res = {"message" : "Information given is not sufficient"}
            return JsonResponse(res, status = 400)
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
            if last_name:
                doc_dict["name"] += " " + last_name
            gender = dr.gender
            doc_dict["gender"] = gender
            speciality = dr.speciality.speciality
            doc_dict["speciality"] = speciality
            fees = dr.fees
            doc_dict["fee"] = fees
            profile_photo = dr.doctor.profile_photo
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
    if not request.user.role.role == "Receptionist":
        res = {"message" : "Feature is only available for the receptionist"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        appointment_query_set = Appointment.objects.all()
        if not appointment_query_set:
            res = {"message" : "success", "data" : {"approved_appointments" : [], "rejected_appointments" : [], "requested_appointments" : [], "appointment_transaction_history" : [], "pending_payments" : []}}
            return JsonResponse(res, status = 200)
        res = {"message" : "success", "data" : {"approved_appointments" : [], "rejected_appointments" : [], "requested_appointments" : [], "appointment_transaction_history" : [], "pending_payments" : []}}
        for appointment in appointment_query_set:
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
            symptoms = appointment.symptoms
            apntmnt_dict["symptoms"] = symptoms
            requested_at = appointment.requested_at.strftime("%d/%b/%Y at %H:%M:%S")
            apntmnt_dict["applied_at"] = requested_at
            requested_for = appointment.requested_for.strftime("%d/%b/%Y")
            apntmnt_dict["requested_for"] = requested_for
            last_name = appointment.preferred_doctor.last_name
            doctor_name = appointment.preferred_doctor.first_name
            if last_name:
                doctor_name += " " + last_name
            apntmnt_dict["preferred_doctor_name"] = doctor_name
            speciality = appointment.preferred_doctor.doctorinfo_set.reverse()[0].speciality.speciality
            apntmnt_dict["doctor_speciality"] = speciality
            appointment_info_query_set = appointment.appointmentinfo_set.reverse()
            if not appointment_info_query_set:
                res["data"]["requested_appointments"].append(apntmnt_dict)
            else:
                appointment_info_obj = appointment_info_query_set[0]
                if appointment_info_obj.receptionist_approval_status == False and appointment_info_obj.rejection_status == False:
                    res["data"]["requested_appointments"].append(apntmnt_dict)
                if appointment_info_obj.receptionist_approval_status == True and appointment_info_obj.rejection_status == False and appointment_info_obj.prescription_status == False:
                    if appointment_info_obj.payment_status:
                        apntmnt_dict["payment_status"] = "Paid"
                    else:
                        apntmnt_dict["payment_status"] = "Unpaid"
                    if appointment_info_obj.doctor_approval_status:
                        apntmnt_dict["doctor_approval_status"] = "Approved"
                    else:
                        apntmnt_dict["doctor_approval_status"] = "Not Approved"
                    res["data"]["approved_appointments"].append(apntmnt_dict)
                if appointment_info_obj.rejection_status == True:
                    if appointment_info_obj.receptionist_approval_status:
                        apntmnt_dict["receptionist_approval_status"] = "Accepted"
                        if appointment_info_obj.payment_status:
                            apntmnt_dict["payment_status"] = "Paid"
                            if appointment_info_obj.doctor_approval_status:
                                apntmnt_dict["doctor_approval_status"] = "Approved"
                            else:
                                apntmnt_dict["doctor_approval_status"] = "Rejected"
                                apntmnt_dict["remark"] = appointment_info_obj.remark
                                apntmnt_dict["payment_status"] = "Will be refunded"
                        else:
                            apntmnt_dict["payment_status"] = "Unpaid"
                            apntmnt_dict["doctor_approval_status"] = "NA"
                    else:
                        apntmnt_dict["receptionist_approval_status"] = "Not Approved"
                        apntmnt_dict["remark"] = appointment_info_obj.remark
                        apntmnt_dict["doctor_approval_status"] = "NA"
                        apntmnt_dict["payment_status"] = "NA"
                    res["data"]["rejected_appointments"].append(apntmnt_dict)
                if appointment_info_obj.receptionist_approval_status == True and appointment_info_obj.payment_status == False and appointment_info_obj.rejection_status == False:
                    res["data"]["pending_payments"].append(apntmnt_dict)
                if appointment_info_obj.payment_status == True and appointment_info_obj.prescription_status == True:
                    appointment_id = appointment.id
                    # payment = appointment.paymentdetails_set.values("id", "amount")
                    # payment_id = payment[0]
                    # amount_paid = payment[1]
                    apntmnt_dict["payment_id"] = 7
                    apntmnt_dict["amount_paid"] = 5000000
                    res["data"]["appointment_transaction_history"].append(apntmnt_dict)
        return JsonResponse(res ,status = 200)
    elif request.method == "PATCH":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        if not appointment_id:
            res = {"message" : "Information given is not suffcient"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id)
        if not appointment_query_set:
            res = {"message" : "There is no such appointment with such id"}
            return JsonResponse(res, status = 202)
        appointment_obj = appointment_query_set[0]
        appointment_info_query_set = appointment_obj.appointmentinfo_set.reverse()
        if not appointment_info_query_set:
            appointment_obj.appointmentinfo_set.create(receptionist_approval_status = True, last_modified_by_receptionist = datetime.datetime.now())
            res = {"message" : "Appointment has been approved succesfully and sent to the respective doctor for his/her approval"}
            send_payment_request_mail(appointment_obj.requested_at.strftime("%d/%b/%Y at %H:%M:%S"), "abhay.2327cseml1085@kiet.edu", datetime.datetime.now(), appointment_obj.preferred_doctor.first_name)
            return JsonResponse(res, status = 201)
        else:
            appointment_info_obj = appointment_info_query_set[0]
            if appointment_info_obj.receptionist_approval_status == True and appointment_info_obj.rejection_status == False:
                if appointment_info_obj.doctor_approval_status == True:
                    res = {"message" : "Patient is already approved to meet the doctor"}
                    return JsonResponse(res, status = 409)
                else:
                    res = {"message" : "Appointment is one step behind to get the prescription"}
                    return JsonResponse(res, status = 409)
            else:
                if appointment_info_obj.receptionist_approval_status == False:
                    appointment_obj.appointmentinfo_set.values().update(receptionist_approval_status = True, last_modified_by_receptionist = datetime.datetime.now())
                    res = {"message" : "Appointment has been approved succesfully and sent to the respective doctor for his/her approval"}
                    send_payment_request_mail(appointment_obj.requested_at.strftime("%d/%b/%Y at %H:%M:%S"), "abhay.2327cseml1085@kiet.edu", datetime.datetime.now(), appointment_obj.preferred_doctor.first_name)
                    return JsonResponse(res, status = 201)
                else:
                    res = {"message" : "Appointment request is sent to doctor for their approval"}
                    return JsonResponse(res, status = 409)
    elif request.method == "DELETE":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        if not appointment_id:
            res = {"message" : "Information given is not sufficient"}
            return JsonResponse(res, status = 400)
        remark = data.get("remark")
        if not remark:
            res = {"message" : "Remark is required !!!"}
            return JsonResponse(res, status = 400)
        appointment_query_set = Appointment.objects.filter(id = appointment_id)
        if not appointment_query_set:
            res = {"message" : "appointment_id does not exist"}
            return JsonResponse(res, status = 400)
        appointment_obj = appointment_query_set[0]
        appointment_info_query_set = appointment_obj.appointmentinfo_set.values()
        if not appointment_info_query_set:
            appointment_obj.appointmentinfo_set.create(rejection_status = True, remark = remark, last_modified_by_receptionist = datetime.datetime.now())
            res = {"message" : "Appointment has been rejected successfully"}
            return JsonResponse(res, status = 200)
        else: 
            appointment_info_obj = appointment_info_query_set[0]
            if appointment_info_obj.rejection_status == False:
                appointment_obj.appointmentinfo_set.values().update(rejection_status = True, last_modified_by_receptionist = datetime.datetime.now, remark = remark)
                res = {"message" : "Appointment has been rejected successfully"}
                return JsonResponse(res, status = 200)
            else:
                res = {"message" : "Appointment is already rejected"}
                return JsonResponse(res, status = 400)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)

def get_profile(request):
    if not request.user.is_authenticated:
        res = {"message" : "Login is required"}
        return JsonResponse(res, status = 401)
    if not request.user.is_staff:
        res = {"message" : "Only receptionist can see his profile"}
        return JsonResponse(res, status = 403)
    if request.method == "GET":
        profile_obj = CustomUser.objects.filter(id = request.user.id).values("id", "first_name", "last_name", "email", "phone_number")
        res = dict(profile_obj)
        return JsonResponse(res, status = 200)
    else:
        res = {"message" : "Invalid request method"}
        return JsonResponse(res, status = 405)