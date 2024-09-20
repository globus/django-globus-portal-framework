.. _generic_views_reference:

Generic Class-Based Views
=========================

Generic views allow for more fine-grained customization of Django Globus Portal Framework viwes.
They are built on Django Generic Class-Based views. DGPF generic views should be inherited with
specific desired functionality overridden. The URL conf also needs to be updated to override the
original DGPF views.

An example here shows usage of a class-based view which requires login and allows extending filters:

.. code-block:: python

    # views.py
    from django.contrib.auth.mixins import LoginRequiredMixin
    from globus_portal_framework.views.generic import SearchView


    class MyCustomSearchView(LoginRequiredMixin, SearchView):

        @property
        def filters(self):
            """Allow custom default_filters per-index in settings.py"""
            return super().filters + self.get_index_info().get('default_filters', [])

And here shows overriding the built-in DPGF Search View in ``urls.py``:

.. code-block:: python

    # urls.py
    from django.urls import path, include
    import globus_portal_framework.urls  # Allows index converter usage
    from testportal.views import MyCustomSearchView

    urlpatterns = [
        path("<index:index>/", MyCustomSearchView.as_view(), name="search"),

        # Note, you must define your custom view above the originals for Django to use it!
        path("", include("globus_portal_framework.urls")),
    ]

.. automodule:: globus_portal_framework.views.generic
   :members:
   :member-order: bysource
   :show-inheritance:
