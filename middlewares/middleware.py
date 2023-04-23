import logging
import time

from django.shortcuts import redirect, render
from django.urls import reverse

# def process_response(request, response):
#     if response.status_code == 404:
#         time.sleep(5)
#         return redirect('/', permanent=False)
#     return response

logger = logging.getLogger('django')


class PageNotFoundMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            response = render(request, '404.html', status=404)
        return response
