.. _gclients_reference:


Globus Clients
==============

The `globus_portal_framework.gsearch` module exposes utilities for loading
saved user tokens from the database and using them in views. A common view may look
like:

.. code-block::

    @login_required
    def hello_flow(request):
        log.debug(f"Loading flow token for user {request.user.username}")
        token = load_globus_access_token(request.user, settings.FLOW_ID)
        authorizer = globus_sdk.AccessTokenAuthorizer(token)
        sfc = globus_sdk.SpecificFlowClient(settings.FLOW_ID, authorizer=authorizer)

Django Globus Portal Framework directly uses most Globus Services. However, if you
use one not listed here or define your own, you will need to setup a scope for that service.
See ``SOCIAL_AUTH_GLOBUS_SCOPE`` in :ref:`settings_example` for adding extra scopes.

.. warning::

    DGPF currently only supports static scopes. Newly added static scopes will require
    existing users to logout and login again before tokens will be available for the new
    view.


.. automodule:: globus_portal_framework.gclients
   :members:
   :member-order: bysource
   :show-inheritance:
