from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from account.permissions import IsEducationOfficerOrAdmin
from education.models import School, SchoolContactPerson
from education.serializers import (
    SchoolContactPersonModelSerializer,
    SchoolModelSerializer,
)


class SchoolModelViewSet(ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = School.objects.all()
    serializer_class = SchoolModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)

    def finalize_response(
        self,
        request: Request,
        response: Response,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        if isinstance(response.data, dict) and response is not None:
            response.data = {"status": response.status_code, "result": response.data}
        elif isinstance(response.data, list) and response is not None:
            response.data = {"status": response.status_code, "results": response.data}

        return super().finalize_response(request, response, *args, **kwargs)


class SchoolContactPersonModelViewSet(ModelViewSet):
    http_method_names = ("get", "post", "put", "patch", "delete")
    queryset = SchoolContactPerson.objects.all()
    serializer_class = SchoolContactPersonModelSerializer
    permission_classes = (IsAuthenticated, IsEducationOfficerOrAdmin)

    def finalize_response(
        self,
        request: Request,
        response: Response,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        if isinstance(response.data, dict) and response is not None:
            response.data = {"status": response.status_code, "result": response.data}
        elif isinstance(response.data, list) and response is not None:
            response.data = {"status": response.status_code, "results": response.data}

        return super().finalize_response(request, response, *args, **kwargs)
