from django.urls import path

from finance.views import HomeAPIView

app_name = "finance"

urlpatterns = [
    path("", HomeAPIView.as_view(), name="home"),
]
