import logging
import traceback
from http import HTTPStatus

import requests
from te_django_health_check.health_check import store_health_check_data

from weather_service.constants import constant
from weather_service.serializers import BaseResponseSerializer
from weather_service.settings import TIMEOUT, TOTAL_ATTEMPT
from weather_service.utils.exceptions import WeatherValidationError

logger = logging.getLogger(__name__)


def check_timeout_and_retry_attempts(url, action, api_name, payload=None, headers=None):
    """
    This function checks the response in delay time and given attempts.

    :param url: URL is a string value for the 3rd party API.
    :type url: string
    :param action: action is the method for the URL.
    :type action: string
    :param api_name: 3rd party vendor API name.
    :type api_name: string
    :param payload: payload is the json object for the URL.
    :type payload: JSON object, optional
    :param headers: headers is the json object for the URL.
    :type headers: JSON object, optional
    :raises APIException: If the total attempts over then raises the exception.
    :return: Return the json object fetched from the 3rd party API.
    :rtype: JSON object
    """
    response = {}
    for attempt in range(TOTAL_ATTEMPT):
        error_message = None
        try:
            api_request = getattr(requests, action)
            # reference from https://requests.readthedocs.io/en/master/user/quickstart/#timeouts
            response = api_request(url, payload, headers=headers, timeout=TIMEOUT)
            # Storing data for health check of dark sky API.
            error_message = (
                response.json().get("error") if response.json().get("error") else None
            )
            store_health_check_data(api_name, response.status_code, error_message)
            if response.status_code == 200:
                break
            logger.error(f"{response.json()['error']} for attempt : {attempt + 1}")
        except Exception:
            logger.error("uncaught exception: %s", traceback.format_exc())

        if attempt == TOTAL_ATTEMPT - 1:
            error_message = (
                error_message
                if error_message
                else "Vendor API failed for all retries attempt."
            )
            logger.error(
                "All retries attempt are exhausted and the final log is : "
                + str(error_message)
            )
            WeatherValidationError.status_code = HTTPStatus.GATEWAY_TIMEOUT
            raise WeatherValidationError(
                BaseResponseSerializer.error_response(
                    {constant["Error"]: error_message},
                    HTTPStatus.GATEWAY_TIMEOUT,
                    message=constant["BadRequestMessage"],
                ).data
            )

    logger.info("Get success response from the vendor request.")
    # return response of 3rd party API.
    return response
