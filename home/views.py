import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone


def current_time(request):
    data = {'time': timezone.now(), 'req': request.path}  # , 'request': request
    return JsonResponse(data)


# Create your views here.
def home(request):
    return render(request, 'home.html',
                  {'current': datetime.datetime.now()})
