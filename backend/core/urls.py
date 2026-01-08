from django.urls import path
from .views import SismoListAPIView

urlpatterns = [
    path("sismos/", SismoListAPIView.as_view(), name="sismos-list"),
]