from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def ping(request):
    return HttpResponse("venues app is alive")