Installation and Setup
======================

Install the packages below to get started. Globus Portal Framework requires Python
3.7 and higher.

.. code-block:: bash

  pip install django-admin django-globus-portal-framework

Django-admin will help you bootstrap your initial portal while Globus Portal Framework will
add tooling for Globus services, Search, Transfer, and Auth.

Run the ``django-admin`` command below to create your project layout.

.. code-block:: bash

  django-admin startproject myportal
  cd myportal

This will create your basic Django project with the following project structure:

.. code-block::

  myportal/
    db.sqlite3
    manage.py
    myportal/
      settings.py
      urls.py

Globus Auth
-----------

Globus Auth will allow your users to login to the portal, storing their tokens in
the database for Search, Transfer, or any other custom functionality you want to
implement.

You'll need a Client ID from Globus. Follow `these instructions <https://docs.globus.org/api/auth/developer-guide/#register-app>`_
from the Globus Auth Developer Guide.

When you register your application with Globus, make sure it has the following settings:

* **Redirect URL** -- ``http://localhost:8000/complete/globus/``
* **Native App** -- `Unchecked`

Settings
--------

Next, you will need to modify your ``myportal/settings.py`` file to enable user
auth and Globus Portal Framework components. You can copy-paste the individual
settings below, or use our refer to our :ref:`settings_example` for a complete
``settings.py`` file reference.

.. code-block:: python

  # Your portal credentials for a Globus Auth Flow
  SOCIAL_AUTH_GLOBUS_KEY = 'Put your Client ID here'
  SOCIAL_AUTH_GLOBUS_SECRET = 'Put your Client Secret Here'

  # This is a general Django setting if views need to redirect to login
  # https://docs.djangoproject.com/en/3.2/ref/settings/#login-url
  LOGIN_URL = '/login/globus'

  # This dictates which scopes will be requested on each user login
  SOCIAL_AUTH_GLOBUS_SCOPE = []

  # Installed apps tells Django which packages to load on startup
  INSTALLED_APPS = [
      ...
      'globus_portal_framework',
      'social_django',
  ]

  # Middleware provides exception handling
  MIDDLEWARE = [
      ...
      'globus_portal_framework.middleware.ExpiredTokenMiddleware',
      'globus_portal_framework.middleware.GlobusAuthExceptionMiddleware',
      'social_django.middleware.SocialAuthExceptionMiddleware',
  ]

  # Authentication backends setup OAuth2 handling and where user data should be
  # stored
  AUTHENTICATION_BACKENDS = [
      'globus_portal_framework.auth.GlobusOpenIdConnect',
      'django.contrib.auth.backends.ModelBackend',
  ]

  # The context processor below provides some basic context to all templates
  TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                ...
                'globus_portal_framework.context_processors.globals',
            ],
        },
    },
  ]


Add the base URLs for Globus Portal Framework in your ``myportal/urls.py`` file.
These will provide a starting point for your Globus Portal. You may keep or discard
any existing paths in your ``urlpatterns``.

.. code-block:: python

  from django.urls import path, include

  urlpatterns = [
      # Provides the basic search portal
      path('', include('globus_portal_framework.urls')),
      # Provides Login urls for Globus Auth
      path('', include('social_django.urls', namespace='social')),
  ]

Now run your server to see your Globus Portal. Migrate will setup your database,
which will be used in the next section when adding Globus Auth. The second command
will run your Globus Portal.

.. code-block:: bash

  python manage.py migrate
  python manage.py runserver

You should now be able to view a portal at http://localhost:8000/