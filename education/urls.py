from django.urls import path

from education.views import HomeAPIView

app_name = "education"

urlpatterns = [
    path("", HomeAPIView.as_view(), name="home"),
]
