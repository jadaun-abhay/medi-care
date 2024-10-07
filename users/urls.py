from django.urls import path

from users import views

urlpatterns = [
    path("", views.index),
    path("login/", views.login),
    path("logout/", views.logout),
]