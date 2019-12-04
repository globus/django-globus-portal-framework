# Django Globus Portal Framework

Globus Portal Framework is a collection of tools for quickly bootstrapping a
portal for Globus Search. Use the guide below to get your portal running with
Globus Auth and your custom search data. After that, you can make your data
more accessible with Globus Transfer, or extend it how you want with your custom
workflow.

## Requirements

* Python 3.5 or higher
* Django 2.2, 3.0

## Quick-Start Guide

Let's get started with a simple Globus Search portal.

```
    $ pip install django-admin
    $ pip install -e git+https://github.com/globusonline/django-globus-portal-framework#egg=django-globus-portal-framework
    $ django-admin startproject myproject
    $ cd myproject
```

You'll need a Client ID from Globus. Follow [these instructions](https://docs.globus.org/api/auth/developer-guide/#register-app)
from the Globus Auth Developer Guide.

For your portal, ensure your Globus App has these settings:

* **Redirect URL**--http://localhost:8000/complete/globus/
* **Native App**--Unchecked


In your myproject/settings.py file, add the following settings to your
project's `settings.py` file. Existing Django settings are hidden by `...`.
```
SOCIAL_AUTH_GLOBUS_KEY = 'Put your Client ID here'
SOCIAL_AUTH_GLOBUS_SECRET = 'Put your Client Secret Here'


SEARCH_INDEXES = {
    # Leave this blank to show the built-in test index
    # 'your-index-here': {}
}

INSTALLED_APPS = [
    ...
    'globus_portal_framework',
    'social_django',
]

MIDDLEWARE = [
    ...
    'globus_portal_framework.middleware.ExpiredTokenMiddleware',
    'globus_portal_framework.middleware.GlobusAuthExceptionMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

SOCIAL_AUTH_GLOBUS_SCOPE = [
    'urn:globus:auth:scope:search.api.globus.org:search',
]

AUTHENTICATION_BACKENDS = [
    # A more feature rich version of Python Social Auth for Django.
    'globus_portal_framework.auth.GlobusOpenIdConnect',
    'django.contrib.auth.backends.ModelBackend',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'myproject', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                ...
                'globus_portal_framework.context_processors.globals',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]
```

Now, add your URLs in your `myproject/urls.py` file. These will provide
`/login` and `/logout` URLs in addition to index urls at `/myindex/`. Index
URLs are created automatically by the keys in your `SEARCH_INDEXES` variable
in your `settings.py` file.

```
from django.urls import path, include

urlpatterns = [
    # Provides the basic search portal
    path('', include('globus_portal_framework.urls')),
    # (OPTIONAL) Provides debugging for your Globus Search Index result data
    path('', include('globus_portal_framework.urls_debugging')),
    # (RECOMMENDED) Provides Login urls for Globus Auth
    path('', include('social_django.urls', namespace='social')),
]
```

Do your initial database migration and run your local server. The `manage.py`
script was created by `django-admin startproject` and should be in the top
level of your project directory.

```
    $ python manage.py migrate
    $ python manage.py runserver
```

## Customizing Your Portal

This gives you a basic portal with Globus Auth and Globus Search. From here, you
will likely want to request a search index to setup your custom portal. Send an
email to support@globus.org with a brief description of what you want. Once you have
a search index, See the resources below for customizing it to your needs:

* [Configuring Your Index](https://github.com/globusonline/django-globus-portal-framework/wiki/Configuring-Your-Index) -- Configure the basics for your index
* [Configuring Facets](https://github.com/globusonline/django-globus-portal-framework/wiki/Configuring-Facets) -- Configure facets for filtering search results
* [Customzing Fields and Templates](https://github.com/globusonline/django-globus-portal-framework/wiki/Customizing-Fields-and-Templates) -- Show users your custom search data
* [Adding Transfer and Preview](https://github.com/globusonline/django-globus-portal-framework/wiki/Adding-Transfer-and-Preview) -- Enrich your search results

See a minimal complete project here for reference (Requires Permission): [DGPF Example App](https://github.com/globusonline/dgpf-example-app)

Extended Features

* [DGPF Confidential Client](https://github.com/globusonline/dgpf-confidential-client) (Requires Permission) -- Secure your raw search record data from user access


