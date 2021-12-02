import logging
import traceback
from datetime import datetime
from http import HTTPStatus

from django.db.models import Q

from service_objects.services import Service

from db.models import Location
from weather_service.constants import constant
from weather_service.serializers import (
    BaseResponseSerializer,
    WeatherResponseSerializer,
)
from weather_service.settings import WEATHER_STALE_DATA_SECONDS
from weather_service.utils import interface
from weather_service.utils.exceptions import UnexpectedError, WeatherValidationError
from weather_service.utils.save_weather_data import (
    aggregate_weather_data_for_te_weather,
    fetch_latitude_longitude_from_property_service,
    get_weather_data,
    save_location_data,
    save_weather_forecast_data,
    update_location_data,
)

logger = logging.getLogger(__name__)


class ForecastWeatherService(Service):
    """
    This class inherits the base class ``Service`` and it includes a method ``process`` to fetch weather forecast data.
    """

    def process(self):
        """
        This method includes business logic to fetch weather forecast data.

        :return: return the Json response of the weather forecast data.
        :rtype: dict
        """
        params = self.data.get("data")
        property_id = params.get("propertyId")
        latitude = params.get("latitude")
        longitude = params.get("longitude")
        stale_data_seconds = (
            params.get("staleDataSeconds")
            if params.get("staleDataSeconds")
            else WEATHER_STALE_DATA_SECONDS
        )
        try:
            query = Q()
            if property_id:
                query.add(Q(property_id=property_id), Q.AND)
                latitude, longitude = fetch_latitude_longitude_from_property_service(
                    property_id,
                    self.data.get("token"),
                    self.data.get("Te-Correlation-Id"),
                )
            query.add(
                Q(
                    lat=latitude,
                    long=longitude,
                    timezone__gte=int(datetime.now().strftime("%s"))
                    - stale_data_seconds,
                ),
                Q.AND,
            )
            location = Location.objects.filter(query).last()
            if not location or stale_data_seconds == 0:
                te_weather_data_list = get_weather_data(latitude, longitude)
                aggregated_data = aggregate_weather_data_for_te_weather(
                    te_weather_data_list
                )
                location = save_location_data(property_id, latitude, longitude)
                for data in te_weather_data_list:
                    if data.get("visualCrossingData"):
                        interface.save_visual_weather_data(
                            location, data.get("visualCrossingData")
                        )
                    else:
                        interface.save_aeris_data(location, data.get("aerisData"))
                interface.save_wather_aggregated_data(location, aggregated_data)
                serializer = WeatherResponseSerializer(location)
                return serializer.data, HTTPStatus.OK
            serializer = WeatherResponseSerializer(location)
            logger.info("Weather data return successfully from service.")
            return serializer.data, HTTPStatus.OK
        except WeatherValidationError as err:
            logger.error(str(err))
            raise err
        except Exception:
            logger.error("uncaught exception: %s", traceback.format_exc())
            raise UnexpectedError(
                BaseResponseSerializer.error_response(
                    {constant["Error"]: constant["SomethingWentWrong"]},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=constant["SomethingWentWrong"],
                ).data
            )
