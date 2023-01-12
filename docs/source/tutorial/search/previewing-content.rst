.. _previewing_content:


Previewing Content
==================

Most Globus Connect Server Collections support HTTPS as a way to access files
on a Globus Collection. For portals in Django Globus Portal Framework, this
prodives a way to display content directly in overview pages or search results.
For example, if each search result in a science portal embeds an image that
conveys the quality of the dataset, it can significantly improve the search
experience for users. In addition, static resources can be used to improve the
look of any static info pages, like in the example below:

.. image:: ../../static/previewing-content.jpeg
  :width: 100%
  :alt: Django Globus Portal Framework with an image showing the APS


Displaying Public Images
------------------------

For public images, the process is only a matter of constructing a valid link
to the Globus Collection, and the image will be displayed when the page loads.
Most GCSv5.4 collections support an HTTPS URL for this exact purpose. The domain name
for a collection can be found by searching collections on the `Globus Webapp <https://app.globus.org/collections>`_
or via the Globus CLI:

.. code-block::

    $ globus collection show my-collection-uuid
    Display Name:                my-collection
    ...
    HTTPS URL:                   https://g-7581c.fd635.8444.data.globus.org

Links to files on a collection contain the HTTPS URL as a domain name in addition to
path to the desired file. Note the path must be correct, and the directory on the
collection must be shared with Public. The URL can be used on HTML img tags like the
example below:

.. code-block:: html

    <img src="https://g-7581c.fd635.8443.data.globus.org/portal/public/APS_aerial.jpeg" width="50%">

Non-Image Content
-----------------

Files on a Globus Collection can be `accessed via GET requests <https://docs.globus.org/globus-connect-server/v5/https-access-collections/#accessing_data>`_.
Typically this involves some javascript code to make the GET request, then dynamically attaching it
to an HTML tag. Numerous examples exist online for `making the request <https://www.w3schools.com/js/js_ajax_http_send.asp>`_
and `attaching response text to elements <https://www.w3schools.com/js/js_htmldom_elements.asp>`_.


Private Content Over HTTPS
--------------------------

Accessing non-public data from a collection over HTTPS is a much more involved process,
and requires making the request to the file using an authorized access token for the
GCS Collection. More info on making authorized requests to a
`Globus Collection can be found here <https://docs.globus.org/globus-connect-server/v5/https-access-collections/#accessing_data>`_.

Django Globus Portal Framework can be configured to request the data_access scope above by
adding the scope to the ``SOCIAL_AUTH_GLOBUS_SCOPE`` variable in ``settings.py``. The token
can be loaded for each user using the following `Django view <https://docs.djangoproject.com/en/4.1/intro/tutorial03/#writing-more-views>`_
below (**Remember to login again to populate the token for your user**):

.. code-block:: python

    from django.http import JsonResponse
    from globus_portal_framework.gclients import load_globus_access_token

    def https_access(request):
        # The resource server for collections is typicaly the collection uuid
        token = load_globus_access_token(request.user, 'globus_collection_uuid')
        return JsonResponse({'http_access_token': token})

.. warning::

    Special care should be taken when exposing user tokens to the browser. With added flexibilty
    comes increased risk. Don't expose tokens which are not needed by front-end applications.

HTTP GET requests using javascript can request private documents from the GCS server by
first requesting the data_access token from the server backend (view above), then making a second
request to the GCS collection with the access token set as the Authorization header as described in
the `Accessing Data section of the GCS Docs <https://docs.globus.org/globus-connect-server/v5/https-access-collections/#accessing_data>`_.

Note that for binary content like images, the HTML ``<img>`` tag cannot provide the authorization header,
meaning the content must be fetched first using javascript and attached manually.

Better support for accessing private documents on Globus Collections is planned at some point in the future.
