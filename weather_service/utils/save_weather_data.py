import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from http import HTTPStatus
from time import time

import pytz
from log_request_id.session import Session
from te_django_health_check.health_check import store_health_check_data

from db.base_models import PublicId
from db.models import (
    ARWeather,
    Location,
    TEWeather,
    VCWeather,
    WeatherData,
    WeatherType,
)
from weather_service.constants import constant
from weather_service.serializers import BaseResponseSerializer
from weather_service.settings import (
    BACKEND_GATEWAY_SERVICE,
    BACKEND_GATEWAY_SERVICE_HOST,
    WEATHER_ACTION_METHOD,
    WEATHER_AERIS_API,
    WEATHER_AERIS_ENABLED,
    WEATHER_VISUAL_CROSSING_API,
    WEATHER_VISUAL_CROSSING_ENABLED,
)
from weather_service.utils import interface
from weather_service.utils.exceptions import WeatherValidationError

logger = logging.getLogger(__name__)

aries_weather_codes = {
    "SNOW": ["BS", "BY", "IP", "RS", "SI", "WM", "S", "SW"],
    "RAIN": ["A", "IC", "L", "R", "RW", "T", "ZL", "ZR", "ZY"],
}
visual_weather_codes = {
    "SNOW": [
        "Blowing Or Drifting Snow",
        "Ice",
        "Heavy Rain And Snow",
        "Light Rain And Snow",
        "Snow",
        "Snow And Rain Showers",
        "Snow Showers",
        "Heavy Snow",
        "Light Snow",
    ],
    "RAIN": [
        "Drizzle",
        "Heavy Drizzle",
        "Light Drizzle",
        "Heavy Drizzle/Rain",
        "Light Drizzle/Rain",
        "Freezing Drizzle/Freezing Rain",
        "Heavy Freezing Drizzle/Freezing Rain",
        "Light Freezing Drizzle/Freezing Rain",
        "Heavy Freezing Rain",
        "Light Freezing Rain",
        "Hail Showers",
        "Lightning Without Thunder",
        "Rain",
        "Rain Showers",
        "Heavy Rain",
        "Light Rain",
        "Squalls",
        "Thunderstorm",
        "Diamond Dust",
        "Hail",
    ],
}
weather_type_names = {"SNOW": 2, "RAIN": 1, "CLEAR": 0}


def epoch_time_converter(time):
    """
    This function is used to convert epoch time into DateTime.

    :param time: time is the epoch time value.
    :type time: int
    :return: return the DateTime response.
    :rtype: int
    """
    logger.info(f"Converting epoch time : {time} into datetime format.")
    return datetime.fromtimestamp(time, tz=pytz.timezone("UTC"))


def make_action_request(url, action, data, service_name):
    """
    This function is used to call the endpoint of micro-services.

    :param url: This data contain url of micro-services.
    :type url: string
    :param action: Action is a http request method like the post, get, etc.
    :type action:
    :param data: This data contain JSON of micro-services.
    :type data: dict
    :param service_name: It contains the TE service name.
    :type service_name: str
    :return: Return the updated dict.
    :raises KeyError: If the key is not valid.
    :rtype: dict
    """
    headers = {
        "Content-type": "application/json; odata=verbose",
        "Accept": "application/json",
    }
    headers.update({"Authorization": data.get("token")})
    headers.update({"Te-Correlation-Id": data.get("Te-Correlation-Id")})
    api_request = getattr(Session(), action)
    response = api_request(url=url, data={}, headers=headers)
    if response.status_code in [200, 201]:
        store_health_check_data(service_name, response.status_code, None)
        logger.info(f"Get success response from {service_name}.")
        return response
    elif response.status_code == 500:
        store_health_check_data(
            service_name, response.status_code, str({"Error": response.reason})
        )
        logger.error(response.reason)
    else:
        store_health_check_data(
            service_name, response.status_code, str(response.json())
        )
        logger.error(response.json())
        return response
    raise Exception(
        BaseResponseSerializer.error_response(
            {constant["Error"]: constant["SomethingWentWrong"]},
            HTTPStatus.INTERNAL_SERVER_ERROR,
            constant["SomethingWentWrong"],
        ).data
    )


def fetch_latitude_longitude_from_property_service(
    property_id, token, te_correlation_id
):
    """
    This function is created to fetch the latitude and longitude from property service.

    :param property_id: public_id of the property object.
    :type property_id: int
    :param token: Token for authentication.
    :type token: str
    :param te_correlation_id: te_correlation_id for the particular request.
    :type te_correlation_id: str
    """
    url = (
        BACKEND_GATEWAY_SERVICE_HOST
        + f"/backend/propertyService/properties/{property_id}/"
    )
    property_response = make_action_request(
        url,
        WEATHER_ACTION_METHOD,
        {
            "token": token,
            "Te-Correlation-Id": te_correlation_id,
        },
        BACKEND_GATEWAY_SERVICE,
    )
    if property_response.status_code != 200:
        logger.error("Failed to fetch property detail.")
        WeatherValidationError.status_code = property_response.status_code
        raise WeatherValidationError(property_response.json())
    logger.info("Property detail fetched successfully.")
    return (
        property_response.json()["data"]["location"]["lat"],
        property_response.json()["data"]["location"]["long"],
    )


def save_location_data(property_id, latitude, longitude):
    """
    This function is created to store the weather forecast data for location model.

    :param property_id: public_id of the property object.
    :type property_id: int
    :param latitude: latitude of a location.
    :type latitude: float
    :param longitude: longitude of a location.
    :type longitude: float
    :return: Return the object of location.
    :rtype: object
    """
    logger.info("store the weather forecast data for location model successfully.")
    return Location.objects.create(
        public_id=PublicId.create_public_id(),
        lat=latitude,
        long=longitude,
        timezone=int(datetime.now().strftime("%s")),
        offset=0,
        property_id=property_id,
    )


def update_location_data(location):
    """
    Updates the location object after changing offset field
    :param location: Location object
    :return:
    """
    location.save(update_fields=["offset"])


def save_weather_type_data(data):
    """
    This function is created to store the weather forecast data for weather type model.

    :param data: This data include the response of weather forecast.
    :type data: json
    :return: Return the object of weather type.
    :rtype: object
    """
    logger.info("store the weather forecast data for weather_type model successfully.")
    return WeatherType.objects.create(
        public_id=PublicId.create_public_id(),
        weather_icon_url="",
        name=data.get("name"),
    )


def save_weather_data(weather_type, data):
    """
    This function is created to store the weather forecast data for weather_data model.

    :param weather_type: This is object of weather_type model.
    :type weather_type: object
    :param data: This data include the response of weather forecast.
    :type data: json
    :return: Return the object of weather_data.
    :rtype: object
    """
    logger.info("store the weather forecast data for weather_data model successfully.")
    return WeatherData.objects.create(
        public_id=PublicId.create_public_id(),
        weather_type=weather_type,
        precip_chance=data.get("precip_chance"),
        precip_water_accumulation=data.get("precip_water_accumulation"),
        temperature=data.get("temperature"),
        day_high_temp=data.get("day_high_temp"),
        day_low_temp=data.get("day_low_temp"),
        precip_snow_accumulation=data.get("precip_snow_accumulation"),
    )


def save_aeris_weather_data(location, weather_data, data):
    """
    This function is created to store the weather forecast data for ar_weather model.

    :param location: location is a object of the location model.
    :type location: object
    :param weather_data: weather_data is a object of the weather_data model.
    :type weather_data: object
    :param data: This data include the response of weather forecast.
    :type data: json
    :return: Return the object of ar_weather model.
    :rtype: object
    """
    logger.info("store the weather forecast data for ar_weather model successfully.")
    weather_type_name = "CLEAR"
    name_set = set(map(str.strip, data.get("name").split(":")))
    for name, values in aries_weather_codes.items():
        if (len(name_set) > 1 and len(name_set.intersection(values)) >= 1) or (
            data.get("name") in values
        ):
            weather_type_name = name
            break
    weather_data.weather_type = WeatherType.objects.get(name=weather_type_name)
    weather_data.save()
    return ARWeather.objects.create(
        public_id=PublicId.create_public_id(),
        location=location,
        weather_data=weather_data,
        forecasted_day=data.get("forecasted_day"),
        timestamp=data.get("timestamp"),
    )


def save_vc_weather_data(location, weather_data, data):
    """
    This function is created to store the weather forecast data for vc_weather model.

    :param location: location is a object of the location model.
    :type location: object
    :param weather_data: weather_data is a object of the weather_data model.
    :type weather_data: object
    :param data: This data include the response of weather forecast.
    :type data: json
    :return: Return the object of vc_weather model.
    :rtype: object
    """
    logger.info("store the weather forecast data for vc_weather model successfully.")
    weather_type_name = "CLEAR"
    name_set = set(map(str.strip, data.get("name").split(",")))
    for name, values in visual_weather_codes.items():
        if (len(name_set) > 1 and len(name_set.intersection(values)) >= 1) or (
            data.get("name") in values
        ):
            weather_type_name = name
            break
    weather_data.weather_type = WeatherType.objects.get(name=weather_type_name)
    weather_data.save()
    return VCWeather.objects.create(
        public_id=PublicId.create_public_id(),
        location=location,
        weather_data=weather_data,
        forecasted_day=data.get("forecasted_day"),
        timestamp=data.get("timestamp"),
    )


def save_te_weather_data(location, weather_data, data):
    """
    This function is created to store the weather forecast data for te_weather model.

    :param location: location is a object of the location model.
    :type location: object
    :param weather_data: weather_data is a object of the weather_data model.
    :type weather_data: object
    :param data: This data include the response of weather forecast.
    :type data: json
    :return: Return the object of te_weather model.
    :rtype: object
    """
    logger.info("store the weather forecast data for te_weather model successfully.")
    weather_data.weather_type = WeatherType.objects.get(name=data.get("name"))
    weather_data.save()
    return TEWeather.objects.create(
        public_id=PublicId.create_public_id(),
        location=location,
        weather_data=weather_data,
        forecasted_day=data.get("forecasted_day"),
        timestamp=data.get("timestamp"),
    )


def save_weather_forecast_data(data, location, key=None):
    """
    This function is created to store the weather forecast data.

    :param key: key is a type of the Third party API name.
    :type key: string
    :param data: This data include the response of weather forecast.
    :type data: dict
    :param location: location is a object of the location model.
    :type location: object
    :return: weather data object
    :rtype: weather data object
    """
    logger.info("store the weather forecast data successfully.")
    weather_data = save_weather_data(None, data)
    if key == WEATHER_VISUAL_CROSSING_API:
        save_vc_weather_data(location, weather_data, data)
    elif key == WEATHER_AERIS_API:
        save_aeris_weather_data(location, weather_data, data)
    else:
        save_te_weather_data(location, weather_data, data)
    return weather_data


def weather_response_optimization(key, data):
    """
    This function is created to optimization the weather forecast data.

    :param data: This data include the response of weather forecast.
    :type data: json
    :param key: key is a type of the Third party API.
    :type key: string
    :return: dict
    :rtype: json
    """
    response = {
        "forecasted_day": None,
        "timestamp": None,
        "name": None,
        "precip_chance": None,
        "precip_water_accumulation": None,
        "temperature": None,
        "day_high_temp": None,
        "day_low_temp": None,
        "precip_snow_accumulation": None,
    }
    if key == WEATHER_VISUAL_CROSSING_API:
        response["forecasted_day"] = data.get("datetime")
        response["timestamp"] = data.get("datetimeEpoch")
        response["name"] = data.get("conditions")
        response["precip_chance"] = data.get("precipprob")
        response["precip_water_accumulation"] = data.get("precip")
        response["temperature"] = data.get("temp")
        response["day_high_temp"] = data.get("tempmax")
        response["day_low_temp"] = data.get("tempmin")
        response["precip_snow_accumulation"] = data.get("snow")

    elif key == WEATHER_AERIS_API:
        response["forecasted_day"] = datetime.strftime(
            datetime.fromisoformat(data.get("dateTimeISO")), "%Y-%m-%d"
        )
        response["timestamp"] = data.get("timestamp")
        response["name"] = data.get("weatherPrimaryCoded")
        response["precip_chance"] = data.get("pop")
        response["precip_water_accumulation"] = data.get("precipIN")
        response["temperature"] = data.get("tempF")
        response["day_high_temp"] = data.get("maxTempF")
        response["day_low_temp"] = data.get("minTempF")
        response["precip_snow_accumulation"] = data.get("snowIN")
    logger.info("optimization the weather forecast data successfully.")
    return response


def get_weather_type(data):
    """
    This function is created to save weather type name.

    :param data: This data include the response of weather forecast.
    :type data: str
    :return: str
    :rtype: str
    """
    weather_type_name = "CLEAR"
    name_set = set(map(str.strip, data.get("name").split(",")))
    for name, values in visual_weather_codes.items():
        if (len(name_set) > 1 and len(name_set.intersection(values)) >= 1) or (
            data.get("name") in values
        ):
            weather_type_name = name
            break
    return weather_type_name


def aggregate_weather_data_for_te_weather(te_weather_data_list):
    """
    This function is used to store aggregated data into the te weather model.

    :param te_weather_data_list: The list of 3rd party objects.
    :type te_weather_data_list: list
    :return: None
    :rtype: list
    """
    final_list = []
    t0 = time()
    te_weather_data_list = [
        data.get("aerisData")
        if data.get("aerisData")
        else data.get("visualCrossingData")
        for data in te_weather_data_list
    ]
    count = len(te_weather_data_list)
    for vendor_data in zip(*te_weather_data_list):
        precip_chance = 0.0
        precip_water_accumulation = 0.0
        temperature = 0.0
        day_high_temp = 0.0
        day_low_temp = 0.0
        options = set()
        precip_snow_accumulation = 0.0
        for data in vendor_data:
            options.add(weather_type_names[get_weather_type(data)])
            precip_chance += (
                data.get("precip_chance")
                if data.get("precip_chance") is not None
                else 0.0
            )
            precip_water_accumulation += (
                data.get("precip_water_accumulation")
                if data.get("precip_water_accumulation") is not None
                else 0.0
            )
            temperature += (
                data.get("temperature") if data.get("temperature") is not None else 0.0
            )
            day_high_temp += (
                data.get("day_high_temp")
                if data.get("day_high_temp") is not None
                else 0.0
            )
            day_low_temp += (
                data.get("day_low_temp")
                if data.get("day_low_temp") is not None
                else 0.0
            )
            precip_snow_accumulation += (
                data.get("precip_snow_accumulation")
                if data.get("precip_snow_accumulation") is not None
                else 0.0
            )
        final_list.append(
            {
                "forecasted_day": vendor_data[0].get("forecasted_day"),
                "timestamp": vendor_data[0].get("timestamp"),
                "name": {0: "CLEAR", 1: "RAIN", 2: "SNOW"}[max(options)],
                "precip_chance": round(precip_chance / count, 2),
                "precip_water_accumulation": round(
                    precip_water_accumulation / count, 2
                ),
                "temperature": round(temperature / count, 2),
                "day_high_temp": round(day_high_temp / count, 2),
                "day_low_temp": round(day_low_temp / count, 2),
                "precip_snow_accumulation": round(precip_snow_accumulation / count, 2),
            }
        )
        logger.debug(f"Aggregate weather data for te_weather: {time() - t0}")
    return final_list


def get_weather_data(lat, long):
    """
    This function is created to get weather data.

    :param lat: This data include the latitude of location.
    :type lat: float
    :param long: This data include the longitude of location.
    :type long: float
    :return: list
    :rtype: list
    """
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        if WEATHER_VISUAL_CROSSING_ENABLED:
            futures.append(
                executor.submit(
                    interface.CallVisualCrossingAPI.fetch_weather_data, *(lat, long)
                )
            )
        if WEATHER_AERIS_ENABLED:
            futures.append(
                executor.submit(interface.CallAerisAPI.fetch_weather_data, *(lat, long))
            )
        return [future.result() for future in as_completed(futures)]
