from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import socket

def send_payment_request_mail(initiation_time, to, acceptance_time, doctor_name, fee = 500):
    content = {"initiation_time" : initiation_time, "acceptance_time" : acceptance_time, "doctor_name" : doctor_name, "fee" : fee}
    html_content = render_to_string("request_payment.html", context=content)
    org_email_content = strip_tags(html_content)

    email = EmailMultiAlternatives("Payment Request for Check-Up", org_email_content, settings.EMAIL_HOST_USER, [to])
    email.attach_alternative(html_content, "text/html")
    email.send()