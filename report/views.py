from django.shortcuts import render


# from django.http import HttpResponse


# Create your views here.

def index(response):
    # return
    return render(response, template_name='reports/report.html')
