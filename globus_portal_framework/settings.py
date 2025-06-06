"""
Django settings for globus_portal_framework project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from globus_portal_framework.constants import FILTER_MATCH_ALL


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

###############################################################################
# Globus Portal Framework Settings
###############################################################################


def get_rfm(search_result):
    if search_result[0].get('remote_file_manifest'):
        return [search_result[0]['remote_file_manifest']]
    else:
        return []


SEARCH_INDEXES = {
    'perfdata': {
        'name': 'Performance Data',
        'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
        'fields': [
            'perfdata',
            ('remote_file_manifest', get_rfm),
            ('globus_http_endpoint',
             lambda x: 'b4eab318-fc86-11e7-a5a9-0a448319c2f8.petrel.host'),
            ('globus_http_scope', lambda x: 'petrel_https_server'),
            ('globus_http_path',
             lambda x: x[0]['remote_file_manifest']['url'].split(':')[2]),

        ],
        'facets': [
            {
                'name': 'Subject',
                'field_name': 'perfdata.subjects.value',
                'size': 10,
                'type': 'terms'
            },
            {
                'name': 'Publication Year',
                'field_name': 'perfdata.publication_year.value',
            },
            {
                'name': 'File Size (Bytes)',
                'type': 'numeric_histogram',
                'field_name': 'remote_file_manifest.length',
                'size': 10,
                'histogram_range': {'low': 15000, 'high': 30000},
            },
            {
                "name": "Dates",
                "field_name": "perfdata.dates.value",
                "type": "date_histogram",
                "date_interval": "month",
            },
        ],
        'filter_match': 'match-all',
        'template_override_dir': 'perfdata',
        'test_index': True,

    }
}

GLOBUS_CLIENT_LOADER = 'globus_portal_framework.gclients.load_globus_client'

SEARCH_RESULTS_PER_PAGE = 10
SEARCH_MAX_PAGES = 10
# This will be the automatic search query when the user loads the page, if
# they have not submitted their own query or there is no query loaded in the
# session. "*" will automatically search everything, but may not be desirable
# if there is a lot of search data in the index, as searches will take a while
DEFAULT_QUERY = '*'
DEFAULT_FILTER_MATCH = FILTER_MATCH_ALL

GLOBUS_NON_USERS_ALLOWED_PUBLIC_ACCESS = True

PREVIEW_DATA_SIZE = 2048

###############################################################################
# General Settings
###############################################################################

# Create 'local_settings.py' and put your below values there to avoid
# accidentally committing them.
# Secret key can be generated with 'openssl rand -hex 32'
SECRET_KEY = '<Add Your Secret Key Here>'
DEBUG = False
# Get your keys at 'developers.globus.org'
SOCIAL_AUTH_GLOBUS_KEY = '<your_Globus_Auth_Client_ID>'
SOCIAL_AUTH_GLOBUS_SECRET = '<your_Globus_Auth_Client_Secret>'

# Set if using POSTGRES
# https://python-social-auth.readthedocs.io/en/latest/configuration/django.html#database  # noqa
# SOCIAL_AUTH_POSTGRES_JSONFIELD = True

ALLOWED_HOSTS = []
INTERNAL_IPS = (
    '127.0.0.1',
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'globus_portal_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Social Django needed for Globus Auth
    'social_django.middleware.SocialAuthExceptionMiddleware',
    # The middleware handles all globus related authentication exceptions.
    # Uncomment if using Globus sessions or/and Globus groups.
    'globus_portal_framework.middleware.GlobusAuthExceptionMiddleware',
    # Redirect to auth page if expired tokens, then back to original page
    'globus_portal_framework.middleware.ExpiredTokenMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'globus_portal_framework.auth.GlobusOpenIdConnect',
    'django.contrib.auth.backends.ModelBackend',
]

SOCIAL_AUTH_SANITIZE_REDIRECTS = False
# Access type needed to get a refresh token
SOCIAL_AUTH_GLOBUS_AUTH_EXTRA_ARGUMENTS = {
    # 'access_type': 'offline',
}

SOCIAL_AUTH_GLOBUS_SCOPE = [
    'urn:globus:auth:scope:search.api.globus.org:search',
    'urn:globus:auth:scope:transfer.api.globus.org:all',
    'https://auth.globus.org/scopes/56ceac29-e98a-440a-a594-b41e7a084b62/all',
    # Optional, only used if you want to restrict users to Globus Groups
    'urn:globus:auth:scope:groups.api.globus.org:'
    'view_my_groups_and_memberships'
]

# Set to True to retrieve information about a user identity from the Globus
# sessions instead of relying on a Globus OIDC userinfo endpoint.
# NOTE! This is required for using SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS
# SOCIAL_AUTH_GLOBUS_SESSIONS = True

# Set to a UUID of a Globus group if you want to restrict access to the portal
# to members of the Globus group.
# Required: The view_my_groups_and_memberships scope above
# Recommended: Add to MIDDLEWARE the following:
#     'globus_portal_framework.middleware.GlobusAuthExceptionMiddleware'
#     This redirects the user for expected exceptions, you need to handle these
#     exceptions yourself if you don't add this.
# SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
#     {
#         'name': 'Portal Users Group',
#         'uuid': 'f63def4d-b472-11e9-af05-0a075bc69d14'
#     }
# ]

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
CSRF_USE_SESSIONS = True

ROOT_URLCONF = 'globus_portal_framework.urls'

BASE_TEMPLATES = 'globus-portal-framework/v2/'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'globus_portal_framework.context_processors.globals',
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'stream': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['stream'],
            # 'handlers': ['null'],  # Quiet by default!
            # 'propagate': False,
            'level': 'WARNING',
        },
        'django.db.backends': {
            'handlers': ['stream'],
            # 'handlers': ['null'],  # Quiet by default!
            # 'propagate': False,
            'level': 'WARNING',
        },
        'globus_portal_framework': {
            'handlers': ['stream'],
            'level': 'DEBUG',
            'propagate': True,
        }
    },
}

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# Override any settings here if a local_settings.py file exists
try:
    from globus_portal_framework.local_settings import *  # noqa
except ImportError:
    pass

# Used to check if this app is running
GLOBUS_PORTAL_FRAMEWORK_DEVELOPMENT_APP = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
