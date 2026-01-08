from django.shortcuts import render

# Create your views here.

from rest_framework import generics
from .models import Sismo
from .serializers import SismoSerializer

class SismoListAPIView(generics.ListAPIView):
    queryset = Sismo.objects.all()
    serializer_class = SismoSerializer