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


In your myproject/settings.py file, add the following below. Existing Django
settings are hidden by `...`.


.. code-block:: bash

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


You will also need to wire up your login URLs in your ``myproject/urls.py`` file:

.. code-block:: bash

  urlpatterns = [
      # Provides the basic search portal
      path('', include('globus_portal_framework.urls')),
      # Provides Login urls for Globus Auth
      path('', include('social_django.urls', namespace='social')),
  ]

You will need to re-migrate your database, since Python Social Auth contains it's
own database tables for user credentials.

Migrate the tables and run your portal:

.. code-block:: bash

  python manage.py migrate
  python manage.py runserver

Your portal should now support Globus Auth http://localhost:8000/
