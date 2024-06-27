.. _custom_urls:

Customizing URLs
----------------

Below is reference information on basic configuration, in addition to more advanced 
customization for broader use-cases. Both info for `urls.py` and template url names are listed. 

Reference URLs
==============

The base URLs for Globus Portal Framework are below:

.. code-block::

    path('<index:index>/', search, name='search'),
    path('<index:index>/detail-preview/<subject>/',
         detail_preview, name='detail-preview'),
    path('<index:index>/detail-preview/<subject>/<endpoint>/<path:url_path>/',
         detail_preview, name='detail-preview'),
    path('<index:index>/detail-transfer/<subject>', detail_transfer,
         name='detail-transfer'),
    path('<index:index>/detail/<subject>/', detail, name='detail'),


You can reverse these URLs via templates with the following:

.. code-block::

  <a href="{% url 'search' 'myindex'  %}">Link to myindex search page</a>
  <a href="{% url 'detail' 'myindex' 'my-globus-search-subject' %}">Link to record detail page</a>
  <a href="{% url 'detail-preview' 'myindex' 'my-globus-search-subject' %}">Link to record preview page</a>
  <a href="{% url 'detail-transfer' 'myindex' 'my-globus-search-subject' %}">Link to record transfer page</a>


Configuring Built-in URLs
=========================

Globus Portal Framework comes built-in with a top level URL you can use to get 
started. Below is all you need to start. 

.. code-block::

  from django.urls import path, include

  urlpatterns = [
      # Provides the basic search portal
      path('', include('globus_portal_framework.urls')),
      # (OPTIONAL) Provides debugging for your Globus Search Index result data
      path('', include('globus_portal_framework.urls_debugging')),
      # (RECOMMENDED) Provides Login urls for Globus Auth
      path('', include('social_django.urls', namespace='social')),
  ]


Configuring Custom URLs
=======================

You can customize URLs in a couple of different ways. The first simple way is to 
keep the view the same but change the URL mapping scheme. This is handy if you 
want to make your URLs look different. For example, you want your search page to be 
`http://myportal.org/science-index/data/`, where 'data' is a new customized URL.

The second customization is adding a custom view instead of the standard DGPF one. 
You can add custom views for one index while keeping the URLs for other indices the same.

Remapping URLs
^^^^^^^^^^^^^^

.. code-block::

  from django.urls import path

  from globus_portal_framework.views import search
  from myportal.views import advanced_search

  urlpatterns = [
      path('<index:index>/data', search, name='search'),
      path('<index:index>/advanced-search', advanced_search, name='advanced-search'),
      path('', include('globus_portal_framework.urls')),
      path('', include('globus_portal_framework.urls_debugging')),
      path('', include('social_django.urls', namespace='social')),
  ]


The URLs above remaps the standard 'search' view to a custom URL. Make sure the 
new mapping is above the other Globus Portal Framework URLs so it takes precedence. 
There is also a custom 'advanced-search' url above, so all indices can use a different 
custom view for different types of searches. 

However, there is a potential problem here. These URLs force ALL urls to use the 
new '/data' URL and '/advanced-search' url. What if you only want one index to 
use Advanced searches?

Remapping Custom Index URLs
===========================

We can register a custom index to use the view we want, and it won't affect URLs 
for other indices. 

.. code-block::

  from django.urls import path
  from globus_portal_framework.urls import register_custom_index
  from myportal.views import advanced_search
  # You can register more than one string to match your index. In this
  # case, we may have another Globus Search index we want to match as a
  # test index. In that case, the test index will re-use all of the prod
  # index views.
  register_custom_index('my_index', ['my-index', 'my-test-index'])

  urlpatterns = [
      path('<my_index>/advanced-search', advanced_search, name='advanced-search'),
      path('', include('globus_portal_framework.urls')),
      path('', include('globus_portal_framework.urls_debugging')),
      path('', include('social_django.urls', namespace='social')),
  ]


Now, `https://my-index/advanced-search` will call `advanced_search()` and all 
other views will call the regular `search()` view and have the search url 
`https://my-other-index/`.
