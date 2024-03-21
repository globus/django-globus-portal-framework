Restricting Login
=================

Many times you don't want just any user that can login to Globus logging into
your app. There are many different levers that can be used to restrict which
users can authenticate to your portal. There are different levels of restrictions,
including restricting by identity provider, restricting by Globus Groups, or whitelisting
by individual users.

Restricting Login by Identity Provider
--------------------------------------


The first common control mechanism exists outside of Django Globus Portal Framework,
and instead can be toggled within the Globus App via the `Required Identity setting <https://docs.globus.org/api/auth/developer-guide/#register-app>`_.
Use the **Requried Identity** setting to control which institutions users can use to login.
For instance, if this is set to The University of Chicago, only users who can login with
a University of Chicago identity will be able to gain access to your portal.

Manage your Globus Apps in the `Developer pages here <https://app.globus.org/settings/developers>`_.

Restricting Login by Globus Groups
----------------------------------

Restricting users by Globus Groups is done with configuration within Django Globus Portal Framework.
Add the following to your settings.py to allow users to login with those groups:

.. code-block:: python

    SOCIAL_AUTH_GLOBUS_ALLOWED_GROUPS = [
        {
            'name': 'My Group 1',
            'uuid': '30be6d85-1983-4d3d-902a-778b1d817aab',
        },
        {
            'name': "My Group 2"
            'uuid': "071a9c9b-043c-43dd-bc03-297086228194",
        }
    ]

The fields above for each group do the following:

* name -- Is any text to describe the group. It will show up on the /allowed-groups page
* uuid -- Is the Globus Group UUID, used for checking membership and linking the group on the /allowed-groups page

Behavior
^^^^^^^^

When a user initiates the login process, they will first login with Globus auth. Django Globus Portal Framework
will then check their memberships with any group configured. If the user has membership in any group, they will
be able to complete the login process. If they are not, they are redirected to the /allowed-groups page. All of
the groups will be listed there, and can be used by the user to request access. After gaining access, users will
be able to login.

Access is granted if a user has any identity with membership in any group. This applies to any linked identities
the user has which have access to a group.

Restricting Login by Whitelists
-------------------------------

The library used for enabling Globus Auth also has a whitelist setting for users. Documentation for
`whitelists can be found here <https://python-social-auth.readthedocs.io/en/latest/configuration/settings.html#whitelists>`_.

For example:

.. code-block:: python

    SOCIAL_AUTH_GLOBUS_WHITELISTED_EMAILS = ['rick@globus.org']

Note, that this does not include any way for users to 'recover' or request access if they are not part of the whitelist.
Users will be rejected with a ``social_core.exceptions.AuthForbidden`` exception, a 500 by default.


Precedence of Evaluation
------------------------

It's generally ok to mix and match each of the above methods. However, each use very different mechanisms and will control
user auth differently. The order of evalutaion is below:


* Globus Auth -- Will reject users if they fail to login with required identity
* Python Social Auth Whitelists -- Will reject any user not in the whitelist
* DGPF Globus Groups -- Will reject users if not in any groups


For example, a portal configured with all three methods, if a user is within a valid configured Globus Group,
but not in the whitelist, the server by default will raise a 500 and disallow the user. For another example,
a portal with all three methonds configured and a user logging in without a valid identity in Globus Auth will
be rejected without the portal checking the whitelist or the users Globus Groups.

