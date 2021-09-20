Installation and Setup
----------------------------

Install the packages below to get started. Globus Portal Framework requires Python
3.7 and higher.

.. code-block:: bash

  pip install django-admin
  pip install -e git+https://github.com/globusonline/django-globus-portal-framework#egg=django-globus-portal-framework


Django-admin will help you bootstrap your initial portal while Globus Portal Framework will
add tooling for Globus services, Search, Transfer, and Auth.

Run the ``django-admin`` command below to create your project layout.

.. code-block:: bash

  django-admin startproject myproject
  cd myproject

This will create your basic Django project with the following project structure:

.. code-block::

  myproject/
    db.sqlite3
    manage.py
    myproject/
      settings.py
      urls.py

Next, modify your ``myproject/settings.py`` file below with the following changes.

.. code-block:: bash

   # Add globus_portal_framework to the bottom of your other INSTALLED_APPS
   INSTALLED_APPS = [
       ...
       'globus_portal_framework',
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


Add the base URLs for Globus Portal Framework in your ``myproject/urls.py`` file.
These will provide a starting point for your Globus Portal. You may keep or discard
any existing paths in your ``urlpatterns``.

.. code-block:: bash

  from django.urls import path, include

  urlpatterns = [
      # Provides the basic search portal
      path('', include('globus_portal_framework.urls')),
  ]

Now run your server to see your Globus Portal. Migrate will setup your database,
which will be used in the next section when adding Globus Auth. The second command
will run your Globus Portal.

.. code-block:: bash

  python manage.py migrate
  python manage.py runserver

You should now be able to view a portal at http://localhost:8000/