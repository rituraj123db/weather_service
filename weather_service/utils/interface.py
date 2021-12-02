import abc
import logging
from datetime import date, timedelta
from http import HTTPStatus
from time import time

from weather_service.settings import (
    WEATHER_ACTION_METHOD,
    WEATHER_AERIS_API,
    WEATHER_AERIS_BASE_URL,
    WEATHER_AERIS_CLIENT_ID,
    WEATHER_AERIS_CLIENT_SECRET,
    WEATHER_AERIS_HOSTNAME,
    WEATHER_DAYS,
    WEATHER_VISUAL_CROSSING_API,
    WEATHER_VISUAL_CROSSING_BASE_URL,
    WEATHER_VISUAL_CROSSING_HOSTNAME,
    WEATHER_VISUAL_CROSSING_KEY,
)
from weather_service.utils import save_weather_data
from weather_service.utils.retries import check_timeout_and_retry_attempts

logger = logging.getLogger(__name__)


class CallWeatherDataAPI(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "fetch_weather_data") and callable(
            subclass.load_data_source
        )


class CallVisualCrossingAPI:
    @staticmethod
    def fetch_weather_data(latitude, longitude):
        """
        This function is created to fetch the weather data from visual crossing API.

        :param latitude: latitude.
        :type longitude: longitude.
        :return: Return the list of weatherData objects for vc_weather.
        :rtype: list
        """
        t0 = time()
        logger.debug(f"Visual crossing API call function time : {t0}")
        BASE_URL = WEATHER_VISUAL_CROSSING_HOSTNAME + WEATHER_VISUAL_CROSSING_BASE_URL
        url = f"{BASE_URL}/{latitude},{longitude}/{str(date.today())}/{date.today() + timedelta(days=WEATHER_DAYS)}?key={WEATHER_VISUAL_CROSSING_KEY}"
        response = check_timeout_and_retry_attempts(
            url, WEATHER_ACTION_METHOD, WEATHER_VISUAL_CROSSING_API
        )
        if response.status_code == HTTPStatus.OK:
            logger.info("Successfully fetch weather data from visual crossing API.")
            logger.debug(f"Visual crossing endpoint timing: {time() - t0}")
            optimized_data = []
            for data in response.json().get("days"):
                optimized_data.append(
                    save_weather_data.weather_response_optimization(
                        WEATHER_VISUAL_CROSSING_API, data
                    )
                )
            return {"visualCrossingData": optimized_data}
        logger.debug(f"Visual crossing endpoint timing: {time() - t0}")
        logger.debug(
            f"Visual crossing endpoint failure response status: {response.status_code}"
        )
        return {}


def save_visual_weather_data(location, visual_crossing_data):
    """
    This function is created to save the weather data from visual crossing API
    """
    vc_weather_data = []
    for data in visual_crossing_data:
        vc_weather_data.append(
            save_weather_data.save_weather_forecast_data(
                data,
                location,
                WEATHER_VISUAL_CROSSING_API,
            )
        )
    logger.info("Successfully save weather data from visual crossing API.")
    return vc_weather_data


class CallAerisAPI:
    @staticmethod
    def fetch_weather_data(latitude, longitude):
        """
        This function is created to fetch the weather data from aeris API.

        :param latitude:latitude.
        :type longitude: longitude.
        :return: Return the list of weatherData objects for ar_weather.
        :rtype: list
        """
        t0 = time()
        logger.debug(f"Aeris API call function time : {t0}")
        BASE_URL = WEATHER_AERIS_HOSTNAME + WEATHER_AERIS_BASE_URL
        url = f"{BASE_URL}/{latitude},{longitude}?filter=mdnt2mdnt&from=today&to=+7days&client_id={WEATHER_AERIS_CLIENT_ID}&client_secret={WEATHER_AERIS_CLIENT_SECRET}"
        response = check_timeout_and_retry_attempts(
            url, WEATHER_ACTION_METHOD, WEATHER_AERIS_API
        )
        if response.status_code == HTTPStatus.OK:
            logger.info("Successfully fetch weather data from Aeris API.")
            logger.debug(f"Aeris endpoint timing: {time() - t0}")
            optimized_data = []
            for data in response.json()["response"][0]["periods"]:
                optimized_data.append(
                    save_weather_data.weather_response_optimization(
                        WEATHER_AERIS_API, data
                    )
                )
            return {"aerisData": optimized_data}
        logger.debug(f"Aeris endpoint timing: {time() - t0}")
        logger.debug(f"Aeris endpoint failure response status: {response.status_code}")
        return {}


def save_aeris_data(location, aeris_data):
    """
    This function is created to save the weather data from aeris API
    """
    aeris_weather_data = []
    for data in aeris_data:
        aeris_weather_data.append(
            save_weather_data.save_weather_forecast_data(
                data,
                location,
                WEATHER_AERIS_API,
            )
        )
    logger.info("Successfully save weather data from Aeris API.")
    return aeris_weather_data


def save_wather_aggregated_data(location, aggregated_data):
    """
    This function is created to save the weather data from aeris API
    """
    aggregated_weather_data = []
    for data in aggregated_data:
        aggregated_weather_data.append(
            save_weather_data.save_weather_forecast_data(data, location)
        )
    logger.info("Successfully save weather aggregated  data.")
    return aggregated_weather_data
