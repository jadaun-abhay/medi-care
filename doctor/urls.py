from django.urls import path

from doctor import views

urlpatterns = [
    path("", views.index),
    path("register/", views.registration),
    path("appointments/", views.appointments),
    path("prescription/", views.give_prescription),
    path("profile/", views.profile),
]