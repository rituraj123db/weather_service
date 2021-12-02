import logging
from http import HTTPStatus

from documentation import swagger_auto_schema
from keycloak_auth.authentication import KeycloakAuthentication
from keycloak_auth.permissions import KeycloakPermission
from rest_framework.viewsets import ViewSet

from weather_service.constants import constant
from weather_service.custom_auto_schema import CustomCodeAutoSchema
from weather_service.document_serializer import (
    WeatherErrorResponseSerializer,
    WeatherSuccessResponseSerializer,
    latitude,
    longitude,
    propertyId,
    staleDataSeconds,
)
from weather_service.serializers import (
    BaseResponseSerializer,
    ForecastWeatherSerializer,
)
from weather_service.services import ForecastWeatherService
from weather_service.settings import WEATHER_USER_SCOPES
from weather_service.utils.exceptions import WeatherValidationError

logger = logging.getLogger(__name__)


class ForecastWeatherView(ViewSet):
    """
    This class inherits the base class ``ViewSet`` and it includes a method ``get`` to fetch current weather data.
    """

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [KeycloakPermission]
    user_scopes = {"GET": WEATHER_USER_SCOPES["WEATHER_GET_METHOD"]}

    @staticmethod
    @swagger_auto_schema(
        auto_schema=CustomCodeAutoSchema,
        manual_parameters=[propertyId, latitude, longitude, staleDataSeconds],
        responses={
            "200": WeatherSuccessResponseSerializer,
            "400": WeatherErrorResponseSerializer,
            "404": WeatherErrorResponseSerializer,
        },
        operation_id="Fetch weather data",
        operation_description="Fetch weather forecast data for a location.",
    )
    def get(request):
        """
        This method is used to fetch current weather data.

        :param request: Request object.
        :type request: request
        :return: Return the Json response to the current forecast with status code.
        :rtype: dict
        """
        if "propertyId" not in request.GET or request.GET.get("propertyId") == "":
            if ("latitude" not in request.GET or request.GET.get("latitude") == "") or (
                "longitude" not in request.GET or request.GET.get("longitude") == ""
            ):
                logger.error(constant["ForecastsRequiredParamsMessage"])
                WeatherValidationError.status_code = HTTPStatus.BAD_REQUEST
                raise WeatherValidationError(
                    BaseResponseSerializer.error_response(
                        {
                            constant["Error"]: [
                                constant["ForecastsRequiredParamsMessage"]
                            ]
                        },
                        HTTPStatus.BAD_REQUEST,
                        message=constant["BadRequestMessage"],
                    ).data
                )

        serialize_data = ForecastWeatherSerializer(data=request.GET)
        if serialize_data.is_valid(raise_exception=False):
            result, status_code = ForecastWeatherService.execute(
                {
                    "data": serialize_data.validated_data,
                    "token": request.headers.get("Authorization"),
                    "Te-Correlation-Id": request.headers.get("Te-Correlation-Id"),
                }
            )
            logger.info("Data return successfully from view.")
            return BaseResponseSerializer.success_response(result, status_code)
        logger.error(str(serialize_data.errors))
        return BaseResponseSerializer.error_response(
            serialize_data.errors,
            HTTPStatus.BAD_REQUEST,
            message=constant["BadRequestMessage"],
        )


class GtepWeatherView(ViewSet):
    """
    Unauthenticated fetch weather data for a location from Gtep
    """

    @staticmethod
    @swagger_auto_schema(
        auto_schema=CustomCodeAutoSchema,
        manual_parameters=[propertyId, latitude, longitude, staleDataSeconds],
        responses={
            "200": WeatherSuccessResponseSerializer,
            "400": WeatherErrorResponseSerializer,
            "404": WeatherErrorResponseSerializer,
        },
        operation_id="Unauthenticated fetch weather data",
        operation_description="Unauthenticated fetch weather forecast data for a location.",
    )
    def get(request):
        return ForecastWeatherView.get(request)
