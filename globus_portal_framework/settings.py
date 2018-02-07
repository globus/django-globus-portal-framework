"""
Django settings for globus_portal_framework project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# Create 'local_settings.py' and put your below values there to avoid
# accidentally committing them.
# Secret key can be generated with 'openssl rand -hex 32'
SECRET_KEY = ''
DEBUG = False
# Get your keys at 'developers.globus.org'
SOCIAL_AUTH_GLOBUS_KEY = '<your_Globus_Auth_Client_ID>'
SOCIAL_AUTH_GLOBUS_SECRET = '<your_Globus_Auth_Client_Secret>'
ALLOWED_HOSTS = []

SEARCH_INDEX = 'mdf'
SEARCH_MAPPER = ('globus_portal_framework.search.utils', 'mdf_to_datacite')
SEARCH_SCHEMA = os.path.join(BASE_DIR, 'globus_portal_framework'
                             '/search/data/mdf_schema.json')
SEARCH_RESULTS_PER_PAGE = 10
SEARCH_MAX_PAGES = 10

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'globus_portal_framework.search'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

AUTHENTICATION_BACKENDS = [
   'globus_portal_framework.auth.GlobusOAuth2',
   'django.contrib.auth.backends.ModelBackend',
]

SOCIAL_AUTH_SANITIZE_REDIRECTS = False
# Access type needed to get a refresh token
SOCIAL_AUTH_GLOBUS_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'offline',
}

# Additional extras
# SOCIAL_AUTH_GLOBUS_SCOPE = [
#     'urn:globus:auth:scope:transfer.api.globus.org:all'
# ]

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
CSRF_USE_SESSIONS = True

ROOT_URLCONF = 'globus_portal_framework.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'globus_portal_framework.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# Override any settings here if a local_settings.py file exists
try:
    from globus_portal_framework.local_settings import *
except ImportError:
    pass
