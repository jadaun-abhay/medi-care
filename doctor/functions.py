import io
from django_renderpdf.helpers import render_pdf
from django.template.loader import render_to_string
from django.conf import settings
from pathlib import Path

def generate_pdf():
    content = {"patient_name" : "Abhay Singh Jadaun", "prescription" : "will be displayed soon", "generated_by" : "doctor_name", "on" : "respective_date"}
    template = "prescription_mail.html"
    file = Path("prescription.pdf")
    file = render_pdf(template= template, file_= file, context= content)
    return file
    
