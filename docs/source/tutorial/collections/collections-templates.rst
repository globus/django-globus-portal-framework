Collections Templates
=====================

Collections has a set of templates that can be modified to better suit the needs
of a portal.

Modifying Templates
-------------------

Let's change the existing templates to add a group at the top of the page, so they
know what groups are associated with a given Collection.

To override templates, first make sure Django knows where your project template
folder is located. Double check ``DIRS`` points to the following:

.. code-block::

  TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [BASE_DIR / 'myproject' / 'templates'],
          'APP_DIRS': True,
          'OPTIONS': {
              'context_processors': [
                  'django.template.context_processors.debug',
                  'django.template.context_processors.request',
                  'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages',
                  'globus_portal_framework.context_processors.globals',
              ],
          },
      },
  ]

The base template for Globus Portal Framework collections is named
`templates/globus-portal-framework/v2/collections-file-manager.html`, so in order
to override the existing template, yours needs to match the name exactly. Create
the file and add the following html:

.. code-block:: html

  {% extends 'globus-portal-framework/v2/collections-file-manager.html' %}

  {%block body%}

  <div class="container">
    <div class="alert alert-info" role="alert">
      {% if globus_portal_framework.collection_data.group_uuid %}
      <a href="https://app.globus.org/groups/{{globus_portal_framework.collection_data.group_uuid}}/about">Join Our Group Here!</a>
      {% else %}
      <p>Our collection is open to all for viewing!</p>
      {% endif %}
    </div>
  </div>

  {{block.super}}
  {% endblock %}


Double check your directory structure to make sure it matches what's below.

.. code-block::

  myproject/
    manage.py
    myproject/
      settings.py
      urls.py
      templates/
        globus-portal-framework/
          v2/
            collections-file-manager.html

Now run your server, and you should see the new changes to your portal!

Checkout the `Django docs <https://docs.djangoproject.com/en/3.1/topics/templates/>`_
for more information about Django Templates.

Template Context
----------------

You'll notice above we had an `if` statement in the template above. Globus Portal
Framework tracks some global context for search indices and collections which is
usable across all templates. For collections, it will populate the following two
items:

* ``globus_portal_framework.collection`` -- The current collection slug
* ``globus_portal_framework.collection_data`` -- Configuration data on the currently selected collection

The first allows developers to determine which collection is being viewed. This can
be handy for modifying the page based on which collection the user has selected.
The second, ``collection_data``, contains all information provided in your
``settings.COLLECTIONS`` variable. You can add a group for your collection above by
adding ``group_uuid`` to the dictionary below:

.. code-block::

  COLLECTIONS = [
      {
          'uuid': '60a0c6af-3f73-453c-afbe-c8504fc428b6',
          'group_uuid': 'my group uuid',
      }
  ]

Collections Templates
---------------------

Every template in Globus Portal Framework can be modified like the template above.
For a full listing if all templates, checkout the `Collection templates here <https://github.com/globus/django-globus-portal-framework/tree/main/globus_portal_framework/templates/globus-portal-framework/v2>`_

