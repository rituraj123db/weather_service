import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from environ import environ

logger = logging.getLogger(__name__)
# SECURITY WARNING: don't run with debug turned on in production!

logger = logging.getLogger(__name__)

root = Path(__file__).parent.parent  # get root of the project

app_dir = f"{root}/weather_service/"

DEBUG = os.environ.get("DEBUG", True)

APPEND_SLASH = False

env = environ.Env()
if DEBUG:
    env.read_env(env_file=f"{app_dir}.env.dev")  # reading .env.dev file
else:
    env.read_env()  # reading .env file

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "o%5=op%1=9-mn&(c-ku%$5dxz)fr%iv@l$@!bn9r%=#rdu6@i2"

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    # "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "weather_service",
    "rest_framework",
    "django_extensions",
    "db",
    "django_mysql",
    "te_django_health_check",
    "documentation",
]

MIDDLEWARE = [
    "log_request_id.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "weather_service.middleware.PageNotFoundMiddleware",
    # "django.contrib.auth.middleware.AuthenticationMiddleware",
    # "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "documentation.middleware.DocumentAuthenticationMiddleware",
]

ROOT_URLCONF = "weather_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "weather_service.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "weather_service",
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
        "OPTIONS": {
            # Tell MySQLdb to connect with 'utf8mb4' character set
            "charset": "utf8mb4"
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = env.str("STATIC_URL")

WEATHER_VISUAL_CROSSING_KEY = env.str("WEATHER_VISUAL_CROSSING_KEY")

# Getting keycloak public key
KEYCLOAK_SERVER_URL = "https://" + str(os.environ.get("CANONICAL_HOSTNAME")) + "/auth/"
KEYCLOAK_PUBLIC_KEY = env("KEYCLOAK_CLIENT_PUBLIC_KEY")
KEYCLOAK_REALM = env("KEYCLOAK_REALM")
SSL_VERIFY = env.bool("SSL_VERIFY")
if KEYCLOAK_PUBLIC_KEY == "key_cloak_realm_public_id":
    import time

    import urllib3

    api_max_call_count = int(env.str("KEYCLOAK_PUBLIC_KEY_API_MAX_CALL_COUNT"))
    sleep_time = int(env.str("KEYCLOAK_PUBLIC_KEY_API_SLEEP_TIME"))  # time in seconds.
    call_count = 1
    while (
        KEYCLOAK_PUBLIC_KEY == "key_cloak_realm_public_id"
        and call_count <= api_max_call_count
    ):
        try:
            urllib3.disable_warnings()
            KEYCLOAK_PUBLIC_KEY = requests.get(
                KEYCLOAK_SERVER_URL + "realms/" + KEYCLOAK_REALM, verify=SSL_VERIFY
            ).json()["public_key"]
            break
        except Exception:
            if (
                set(["-M", "html", "source", "build"]).issubset(sys.argv)
                or "test" in sys.argv
            ):
                break
            logger.error(
                f"Failed to fetch keycloak public key. {call_count}-attempt at {time.ctime()}."
            )
            time.sleep(sleep_time)
            call_count += 1
            KEYCLOAK_PUBLIC_KEY = "key_cloak_realm_public_id"
KEYCLOAK_CLIENT_PUBLIC_KEY = f"""-----BEGIN PUBLIC KEY-----
{KEYCLOAK_PUBLIC_KEY}
-----END PUBLIC KEY-----"""

logger.info("KEYCLOAK_CLIENT_PUBLIC_KEY : " + KEYCLOAK_CLIENT_PUBLIC_KEY)

KEYCLOAK_CONFIG = {
    "AUTH_HEADER_TYPES": (env.str("AUTH_HEADER_TYPES"),),
    "KEYCLOAK_REALM": KEYCLOAK_REALM,
    "KEYCLOAK_CLIENT_ID": env.str("KEYCLOAK_CLIENT_ID"),
    "KEYCLOAK_DEFAULT_ACCESS": env.str("KEYCLOAK_DEFAULT_ACCESS"),
    "KEYCLOAK_METHOD_VALIDATE_TOKEN": env.str("KEYCLOAK_METHOD_VALIDATE_TOKEN"),
    "KEYCLOAK_SERVER_URL": KEYCLOAK_SERVER_URL,
    "KEYCLOAK_CLIENT_SECRET_KEY": env.str("KEYCLOAK_CLIENT_SECRET_KEY"),
    "KEYCLOAK_REALM_PUBLIC_KEY": KEYCLOAK_CLIENT_PUBLIC_KEY,
}

WEATHER_USER_SCOPES = {"WEATHER_GET_METHOD": env.str("WEATHER_GET_METHOD")}

# Time period for health check success and failure counts in last X hrs.
TIME_IN_HOURS = env.int("TIME_IN_HOURS")

WEATHER_VISUAL_CROSSING_API = env.str("WEATHER_VISUAL_CROSSING_API")
WEATHER_ACTION_METHOD = env.str("WEATHER_ACTION_METHOD")
WEATHER_VISUAL_CROSSING_BASE_URL = env.str("WEATHER_VISUAL_CROSSING_BASE_URL")
WEATHER_VISUAL_CROSSING_ENABLED = env.bool("WEATHER_VISUAL_CROSSING_ENABLED")
WEATHER_VISUAL_CROSSING_HOSTNAME = env.str("WEATHER_VISUAL_CROSSING_HOSTNAME")

# Aeris details.
WEATHER_AERIS_CLIENT_ID = env.str("WEATHER_AERIS_CLIENT_ID")
WEATHER_AERIS_CLIENT_SECRET = env.str("WEATHER_AERIS_CLIENT_SECRET")
WEATHER_AERIS_API = env.str("WEATHER_AERIS_API")
WEATHER_AERIS_ENABLED = env.bool("WEATHER_AERIS_ENABLED")
WEATHER_AERIS_HOSTNAME = env.str("WEATHER_AERIS_HOSTNAME")
WEATHER_AERIS_BASE_URL = env.str("WEATHER_AERIS_BASE_URL")

# Health Check Configurations for health check API.
HEALTH_CHECK_CONFIGURATION = {
    WEATHER_VISUAL_CROSSING_API: {
        "action": WEATHER_ACTION_METHOD,
        "url": f"{WEATHER_VISUAL_CROSSING_HOSTNAME + WEATHER_VISUAL_CROSSING_BASE_URL}/{env.str('WEATHER_LATITUDE')},{env.str('WEATHER_LONGITUDE')}/{str(date.today())}/{date.today() + timedelta(days=7)}?key={WEATHER_VISUAL_CROSSING_KEY}",
        "payload": {},
    },
    WEATHER_AERIS_API: {
        "action": WEATHER_ACTION_METHOD,
        "url": f"{WEATHER_AERIS_HOSTNAME + WEATHER_AERIS_BASE_URL}/{env.str('WEATHER_LATITUDE')},{env.str('WEATHER_LONGITUDE')}?filter=day&limit=7&client_id={WEATHER_AERIS_CLIENT_ID}&client_secret={WEATHER_AERIS_CLIENT_SECRET}",
        "payload": {},
    },
}
LOG_REQUEST_ID_HEADER = env("TE_CORRELATION_ID")
REQUEST_ID_RESPONSE_HEADER = env("TE_CORRELATION_ID")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "log_request_id.filters.RequestIDFilter"}},
    "formatters": {
        "standard": {
            "format": "%(levelname)-8s [%(request_id)s] [%(asctime)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": env("LEVEL"),
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "standard",
        },
    },
    "loggers": {
        "weather_service": {
            "handlers": [env("HANDLERS")],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

DOCUMENT_AUTHENTICATION = {
    "OIDC_RP_CLIENT_ID": "te_frontend",
    "OIDC_OP_AUTHORIZATION_ENDPOINT": f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth",
    "OIDC_OP_TOKEN_ENDPOINT": f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
    "OIDC_OP_USER_ENDPOINT ": f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo",
    "OIDC_OP_JWKS_ENDPOINT": f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs",
    "OIDC_OP_LOGOUT_ENDPOINT": f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout",
    "DOCUMENTATION_GET_METHOD": env.str("DOCUMENTATION_GET_METHOD"),
}

# Retries attempt(integer) and timeout(in seconds) for 3rd party vendor.
TOTAL_ATTEMPT = env.int("TOTAL_ATTEMPT")
TIMEOUT = env.int("TIMEOUT")
DOCS_ROOT = os.path.join(BASE_DIR + "/docs/build/html")

BACKEND_GATEWAY_SERVICE_HOST = env.str("BACKEND_GATEWAY_SERVICE_HOST")
BACKEND_GATEWAY_SERVICE = env.str("BACKEND_GATEWAY_SERVICE")
WEATHER_STALE_DATA_SECONDS = env.int("WEATHER_STALE_DATA_SECONDS")
WEATHER_DAYS = env.int("WEATHER_DAYS")
