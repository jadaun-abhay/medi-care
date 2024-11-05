from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("register/", views.registration),
    path("appointments/", views.appointment),
    path("prescription/", views.get_prescription),
    path("profile/", views.profile)
]