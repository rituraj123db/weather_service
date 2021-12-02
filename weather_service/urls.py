"""weather_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import include, path

from documentation.views import FunctionalDocView

from weather_service.custom_auto_schema import schema_view
from weather_service.views import ForecastWeatherView, GtepWeatherView

urlpatterns = [
    path(
        "weatherService/",
        include(
            [
                path(
                    "forecasts/",
                    ForecastWeatherView.as_view({"get": "get"}),
                    name="weather_forecast",
                ),
                path(
                    "forecasts/gtep",
                    GtepWeatherView.as_view({"get": "get"}),
                    name="gtep_weather_forecast",
                ),
            ]
        ),
    ),
    path("version/", include("version_endpoint.urls"), name="version"),
    path("health-check/", include("te_django_health_check.urls"), name="health_check"),
    path(
        "backend/documentation/endpoints/weather-service/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    url(
        r"^backend/documentation/functional/weather-service/(?P<path>.*)$",
        FunctionalDocView.as_view(),
        name="docs_files",
    ),
    path("", include("documentation.urls")),
]
