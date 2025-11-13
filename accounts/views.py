from django.shortcuts import render
from django.http import HttpResponse

def landing(request):
    return HttpResponse("Landing page placeholder")

def home(request):
    return HttpResponse("Home page placeholder")
