Settings
========

Here is a full list of settings allowed by Globus Portal Framework. Adding
these settings to your own `settings.py` file will override the defaults
below.


General Settings
----------------

General settings should apply to most portals.


.. code-block::

  # Configure the general title for your project
  PROJECT_TITLE = 'My Project'



Auth Settings
-------------

.. code-block::

  # Tells Django where your projects login url is
  # Useful for using the ``@login_required`` decorator on custom views
  LOGIN_URL = '/login/globus'

  # Get your keys at 'developers.globus.org'
  # Login is managed primarily by python-social-auth
  SOCIAL_AUTH_GLOBUS_KEY = '<your_Globus_Auth_Client_ID>'
  SOCIAL_AUTH_GLOBUS_SECRET = '<your_Globus_Auth_Client_Secret>'

  # Tells Django how to authenticate users
  AUTHENTICATION_BACKENDS = [
      'globus_portal_framework.auth.GlobusOpenIdConnect',
      'django.contrib.auth.backends.ModelBackend',
  ]

  # Can be used to customize Gloubs Auth.
  # setting access_type to offline enables refresh tokens.
  # WARNING: This can be dangerous.
  SOCIAL_AUTH_GLOBUS_AUTH_EXTRA_ARGUMENTS = {
      'access_type': 'offline',
  }

  # Set scopes what user tokens to request from Globus Auth
  SOCIAL_AUTH_GLOBUS_SCOPE = [
      'urn:globus:auth:scope:search.api.globus.org:search',
      'urn:globus:auth:scope:transfer.api.globus.org:all',
      'urn:globus:auth:scope:groups.api.globus.org:view_my_groups_and_memberships'
  ]


Search Settings
---------------

* ``SEARCH_INDEXES`` -- The main listing of search indexes in your portal


.. code-block::

  # Number of search results that will display on the search page before paginating
  SEARCH_RESULTS_PER_PAGE = 10
  # Max number of pages to display
  SEARCH_MAX_PAGES = 10

  # Default query if no user search or saved session search.
  # Note: This will be slow for an index with a lot of search data.
  DEFAULT_QUERY = '*'
  # Filtering behavior to use for searching across indices.
  # Note: Can be overrided by per-index settings.
  DEFAULT_FILTER_MATCH = FILTER_MATCH_ALL

Templates
---------

.. code-block::

  # Setting for which Globus Portal Framework template set you should use.
  # Mostly for backwards compatibility, but allows for a fully custom set of
  # templates.
  BASE_TEMPLATES = 'globus-portal-framework/v2/'

  # General Template settings. Full example listed for reference, but only
  # the last three context_processors are relevant
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
                  # Social Django context processors for login
                  'social_django.context_processors.backends',
                  'social_django.context_processors.login_redirect',
                  # Globus Portal Framework general context for search indices
                  # and other general context per-template.
                  'globus_portal_framework.context_processors.globals',
              ],
          },
      },
  ]


Under the Hood
--------------

Modify default client loading behavior. Typically only used in [DGPF Confidential Client](https://github.com/globus/dgpf-confidential-client)
```
GLOBUS_CLIENT_LOADER = 'globus_portal_framework.gclients.load_globus_client'
```

