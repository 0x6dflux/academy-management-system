from django.urls import path

from account.views import UserCreateAPIView, UserRetrieveAPIView

app_name = "account"

urlpatterns = [
    path("create-user/", UserCreateAPIView.as_view(), name="create-user"),
    path("me/", UserRetrieveAPIView.as_view(), name="me"),
    path("", UserCreateAPIView.as_view(), name="create-user"),
]
