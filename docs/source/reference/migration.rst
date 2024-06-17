.. _migration_reference:

Migration
=========

Migrating to v0.3.0
-------------------

v0.3.0 introduces a fresh styling for the DGPF portal. You can migrate to the 
new design by changing the following in your own `settings.py`.

.. code-block:: python

  # Changing base_template from v2 to v3
  BASE_TEMPLATES = 'globus-portal-framework/v3/'

You can overwrite the existing templates for the v3 version by replacing the template
files (.html) and styling (.css) in `templates/globus-portal-framework/v3/` and 
`static/globus-portal-framework/v3/` respectively.

.. note::

   In case you want to revert back to the `v2` styling, simply undo the 
   `BASE_TEMPLATES` value in your `settings.py`.

.. warning::

   Breadcrumbs have been removed as part of the default `v3` styling, but users
   are encouraged to add their own styling (if their use cases require the breadcrumb) and 
   uncomment the breadcrumb code segment in `templates/globus-portal-framework/v3/base.html`.