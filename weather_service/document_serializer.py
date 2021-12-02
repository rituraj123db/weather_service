from drf_yasg import openapi
from rest_framework import serializers


class WeatherErrorResponseSerializer(serializers.Serializer):
    """
    This serializer class is used to manage the response of not found in the endpoint document.
    """

    success = serializers.BooleanField(default=False)
    errors = serializers.ListField(required=False)
    data = serializers.JSONField(default={})
    message = serializers.CharField(required=False)
    code = serializers.IntegerField(required=False)


propertyId = openapi.Parameter(
    "propertyId",
    in_=openapi.IN_QUERY,
    description="propertyId",
    type=openapi.TYPE_INTEGER,
    required=False,
)

latitude = openapi.Parameter(
    "latitude",
    in_=openapi.IN_QUERY,
    description="latitude",
    type=openapi.FORMAT_FLOAT,
    required=False,
)

longitude = openapi.Parameter(
    "longitude",
    in_=openapi.IN_QUERY,
    description="longitude",
    type=openapi.FORMAT_FLOAT,
    required=False,
)

staleDataSeconds = openapi.Parameter(
    "staleDataSeconds",
    in_=openapi.IN_QUERY,
    description="staleDataSeconds",
    type=openapi.TYPE_INTEGER,
)


class WeatherTypeSerializer(serializers.Serializer):
    """
    This serializer class is used to manage the response of "forecasts" endpoint in endpoint
    documentation.
    """

    publicId = serializers.IntegerField(source="public_id", required=False)
    weatherIconUrl = serializers.CharField(source="weather_icon_url", required=False)
    name = serializers.CharField(required=False)


class WeatherDataSerializer(serializers.Serializer):
    """
    This serializer class is used to manage the response of "forecasts" endpoint in endpoint
    documentation.
    """

    publicId = serializers.IntegerField(source="public_id", required=False)
    precipChance = serializers.FloatField(source="precip_chance", required=False)
    precipWaterAccumulation = serializers.FloatField(
        source="precip_water_accumulation", required=False
    )
    temperature = serializers.FloatField(required=False)
    dayHighTemp = serializers.FloatField(source="day_high_temp", required=False)
    dayLowTemp = serializers.FloatField(source="day_low_temp", required=False)
    weatherType = WeatherTypeSerializer(source="weather_type", required=False)
    precipSnowAccumulation = serializers.FloatField(
        source="precip_snow_accumulation", required=False
    )


class TEWeatherResponseSerializer(serializers.Serializer):
    """
    This serializer class is used to manage the response of "forecasts" endpoint in endpoint
    documentation.
    """

    publicId = serializers.IntegerField(source="public_id", required=False)
    forecastedDay = serializers.DateField(source="forecasted_day", required=False)
    time = serializers.IntegerField(source="timestamp", required=False)
    weatherData = WeatherDataSerializer(source="weather_data", required=False)


class WeatherResponseSerializer(serializers.Serializer):
    """
    This serializer class is used to manage the response of "forecasts" endpoint in endpoint
    documentation.
    """

    publicId = serializers.IntegerField(source="public_id", required=False)
    propertyId = serializers.IntegerField(source="property_id", required=False)
    lat = serializers.FloatField(required=False)
    long = serializers.FloatField(required=False)
    timezone = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)
    teWeatherData = TEWeatherResponseSerializer(
        source="location_te_weather", many=True, required=False
    )


class WeatherSuccessResponseSerializer(serializers.Serializer):
    """
    This serializer class is used to manage the response of success in the endpoint document.
    """

    success = serializers.BooleanField(default=True)
    data = WeatherResponseSerializer(required=False)
    message = serializers.CharField(required=False)
    code = serializers.IntegerField(required=False)
