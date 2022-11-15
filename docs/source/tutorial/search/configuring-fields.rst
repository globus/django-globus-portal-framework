Built-in Fields
===============

Search Fields take raw search metadata from Globus Search and expose them for
use by templates. Commonly, raw data from Globus Search needs a bit more processing
before it can be viewed in templates. Examples include parsing dates or generating links
to the Globus Webapp. 

Django Globus Portal Framework includes some built-in templates which will automatically
be rendered if given the right field names. Some of these include: 

* Title -- A title for this subject, shown on the search results page and the detail page.
* Globus App Link -- A link to the file on https://app.globus.org.
* HTTPS URL -- A direct-download link to the file.

First, let's take a look at the metadata for the file once more:

.. literalinclude:: ../../examples/simple-ingest-doc.json
   :language: json


Create the following file in ``portal/fields.py`` next to your ``settings.py`` file.

.. literalinclude:: ../../examples/built_in_fields.py
   :language: python


Configure fields for your search index by adding ``fields`` to your ``SEARCH_INDEXES``:


.. code-block:: python

  from myportal import fields

  SEARCH_INDEXES = {
      'index-slug': {
          'name': 'My Search Index',
          'uuid': 'my-search-index-uuid',
          'fields': [
              # Calls a function with your search record as a parameter
              ('title', fields.title),
              ('globus_app_link', fields.globus_app_link),
              ('https_url', fields.https_url)
          ],
      }
  }
