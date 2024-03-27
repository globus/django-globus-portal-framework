.. _urls_reference:

URLs
====

Globus Portal Framework recommends two basic URL includes for most portals: 

* ``globus_portal_framework.urls`` -- Main list of DGPF urls.
* ``social_django.urls`` -- Provides login/auth. See `Python Social Auth Docs <https://python-social-auth.readthedocs.io/en/latest/configuration/django.html>`_

Main URLs
---------

The main ``globus_portal_framework.urls`` include contains a number of urls/views
to get new portals started.


=====================  ==================  ==================================  ========================================
URL Name               Name                Path                                Description
=====================  ==================  ==================================  ========================================
index_selection        `index-selection`   `''`                                 Page for selecting a search index
allowed_groups         `allowed-groups`    `allowed-groups/`                    Lists allowed groups, if configured
search                 `search`            `<index:index>/`                     Search across all records within index
search_about           `search-about`      `<index:index>/about/`               Description of the search index
search_detail          `detail`            `<index:index>/detail/<subject>/`    Details of an individual search result
logout                 `logout`            `logout/`                            Revoke Globus tokens and pop the user session
=====================  ==================  ==================================  ========================================

Overriding a View
^^^^^^^^^^^^^^^^^

You can override a view above with the following. Using the same path as the original
will replace it with the new view. Note that Django will always pick the first URL that
matches, which enables using specific views for specific features and more general views
that are usable by many incides.


.. code-block:: python

    from django.urls import include, path
    import globus_portal_framework.urls  # Allows index converter usage
    from myportal import views

    # Add two custom urls to override original DGPF search-about functionality.
    urlpatterns = [
        # Override for one index only
        path('my-special-index/about/', views.my_special_index_view, name='search-about'),
        # Override all DGPF search_about views
        path('<index:index>/about/', views.search_about, name='search-about'),
        # Include all other DGPF urls
        path('', include('globus_portal_framework.urls')),
        ...
    ]



Index Converters
----------------

The Index Converter is a special URL converter type that matches only to Globus Search
indices listed in the SERACH_INDEXES settings.py variable. Any string which does not match
the list of keys in ``SERACH_INDEXES`` will cause Django to skip that URL and attempt to
match the next one in the list.

This allows Globus Portal Framework to automatically create views for any new index you define.
You may use the index converter type by importing ``globus_portal_framework.views``, although
this isn't typically needed.
