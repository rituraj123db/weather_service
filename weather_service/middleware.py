import json
import logging

from django.http import HttpResponse

logger = logging.getLogger(__name__)


class PageNotFoundMiddleware(object):
    """
    This middleware class is used to handle the page not found error.

    :param object:
    :type object: Object
    :returns: JSON response with status 404.
    :rtype: dict
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            response.status_code == 404
            and "application/json" not in response["content-type"]
        ):
            data = {"Error": f"This url {request.path} not found."}
            logger.error({"Error": f"This url {request.path} not found."})
            response = HttpResponse(
                json.dumps(data), content_type="application/json", status=404
            )
        logger.info("Get success response from middleware.")
        return response
