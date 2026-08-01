from django.urls import path

from account.views import (
    TeacherProfileAPIView,
    UserCreateAPIView,
    UserRetrieveAPIView,
)

app_name = "account"

urlpatterns = [
    path("create-user/", UserCreateAPIView.as_view(), name="create-user"),
    path("me/", UserRetrieveAPIView.as_view(), name="me"),
    path(
        "teacher-profile/",
        TeacherProfileAPIView.as_view(),
        name="teacher-profile",
    ),
]
