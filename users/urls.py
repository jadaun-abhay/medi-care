from django.urls import path

from users import views

urlpatterns = [
    path("", views.index),
    path("login/", views.login),
    path("logout/", views.logout),
    path("specialities/", views.speaciality_list),
    path("get-doctors/", views.get_doctors_under_specific_speciality),
    path("appointments/", views.appointments),
]