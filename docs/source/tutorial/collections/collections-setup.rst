Collections Setup
=================

Setup for a transfer portal requires specifying your Globus Endpoints and configuring
the portal to request users transfer scopes. Users will only be able to view
content they have access.

Edit your `myproject/settings.py` file with the following to enable collections:

.. code-block::

  COLLECTIONS = [
      {
          # Required
          'uuid': '60a0c6af-3f73-453c-afbe-c8504fc428b6',
          # Optional
          'slug': 'airport-climate-data',
          'name': 'Airport Climate Data',
          'path': '/portal/catalog/',
      }
  ]

  SOCIAL_AUTH_GLOBUS_SCOPE = [
      'urn:globus:auth:scope:transfer.api.globus.org:all',
  ]

.. warning::

  Changing scopes will not automatically request new tokens. Users with active
  sessions will need to logout and login again to receive transfer tokens. (we
  will fix this and make it automatic at some point).

Now you can restart your server, login again, and view your collection:

.. code-block::

  python manage.py runserver
