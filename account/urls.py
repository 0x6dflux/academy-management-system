from django.urls import path

from account.views import UserCreateAPIView

app_name = "account"

urlpatterns = [
    path("create-user/", UserCreateAPIView.as_view(), name="create-user"),
    path("", UserCreateAPIView.as_view(), name="create-user"),
]
