.. _configuring_fields:


Passing result fields to templates
====================================
When rendering search results, it is sometimes useful to transform them into a more human-readable format before rendering to a template. (for example: parsing dates or generating links) It may also be useful to fetch "special" fields that will enable built in functionality.  For example the Django Globus Portal Framework includes built-in search result templates which will automatically
render if a search result contains specific field names:

* ``title`` -- A title for a given subject, shown on the search results page and the detail page.
* ``globus_app_link`` -- A link to the file on https://app.globus.org.
* ``https_url`` -- A direct-download link to the file.

You can control what fields are presented to the Django templates, and how these fields are retrieved, using *fields*. The syntax allows you to specify how to find a field either by name, or a retrieval/formatter function.

.. warning::
   Search result templates will always receive two values: 'all' (the entire parsed JSON search result) and 'subject' (the subject ID for the index). Any other template variables must be explicitly specified in the ``fields`` configuration block. This means that you must explicitly specify how to find special template fields such as 'globus_app_link'.

First, let's take a look at the metadata once more:

.. literalinclude:: ../../examples/simple-ingest-doc.json
   :language: json


Create an empty ``myportal/fields.py`` file next to ``settings.py``, and copy-paste the following code.

.. literalinclude:: ../../examples/built_in_fields.py
   :language: python

Here the ``result[0]`` variable encapsulates the information of a given search record, 
and can be used to access any component of the metadata ``content`` such as
``title`` and ``url``.

To propagate ``myportal/fields.py`` throughout your portal, configure fields for your 
search index by adding ``fields`` to your ``SEARCH_INDEXES``:


.. code-block:: python

  from myportal import fields

  SEARCH_INDEXES = {
      "index-slug": {
          "uuid": "my-search-index-uuid",
          **options,  # Other options hidden for brevity
          "fields": [
              # Several syntaxes are available for retrieving a field

              # Fetch the field by name
              "title",

              # Calls a function with your search record as a parameter
              ("globus_app_link", fields.globus_app_link),
              ("https_url", fields.https_url)

              ## Field retrieval/formatters can also be used with custom fields for custom templates
              # Can fetch a field by alias
              ("some_name_in_template", "original_collection_name"),
          ],
      }
  }

You should notice the following changes the next time you run your server:

* `The Search Page <http://localhost:8000/my-index-slug/?q=*>`_
   * "File Number 1" now shows up as the title
* `The Detail Page <http://localhost:8000/my-index-slug/detail/globus%253A%252F%252Fddb59af0-6d04-11e5-ba46-22000b92c6ec%252Fshare%252Fgodata%252Ffile1.txt/>`_
   * The "Transfer/Sync" buttons are now functional

Continue on to cover custom Templates.