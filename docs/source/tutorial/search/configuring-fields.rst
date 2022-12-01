Built-in Fields
===============

Search Fields take raw search metadata from Globus Search and expose them for
use by templates. Commonly, raw data from Globus Search needs a bit more processing
before it can be viewed in templates. Examples include parsing dates or generating links
to the Globus Webapp. 

The Django Globus Portal Framework includes some built-in templates which will automatically
be rendered if given the right field names. Some of these include: 

* Title -- A title for a given subject, shown on the search results page and the detail page.
* Globus App Link -- A link to the file on https://app.globus.org.
* HTTPS URL -- A direct-download link to the file.

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
          ...  # Previous fields hidden for brevity
          "fields": [
              # Calls a function with your search record as a parameter
              ("title", fields.title),
              ("globus_app_link", fields.globus_app_link),
              ("https_url", fields.https_url)
          ],
      }
  }

You should notice the following changes the next time you run your server:

* `The Search Page <http://localhost:8000/my-index-slug/?q=*>`_
   * "File Number 1" now shows up as the title
* `The Detail Page <http://localhost:8000/my-index-slug/detail/globus%253A%252F%252Fddb59af0-6d04-11e5-ba46-22000b92c6ec%252Fshare%252Fgodata%252Ffile1.txt/>`_
   * The "Transfer/Sync" buttons are now functional

Continue on to cover custom Templates.