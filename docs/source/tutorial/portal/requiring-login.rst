Requiring Login
===============

If you need to reach out to Globus Services, such as Transfer, users will need 
to be pre-authenticated so the portal can use their tokens. Django has built-in 
functions to check this, but needs some tuning to work with Python-Social-Auth. 

Make sure you have a working portal with Globus Auth. If not, review the tutorial
documentation and make sure you can login with Globus. 

Settings
^^^^^^^^

First, tell Django where your login link is. For Python Social Auth, the link
below will work fine. 

.. code-block:: 

    LOGIN_URL = '/login/globus'

Views
^^^^^


Now, you can define your views like this:

.. code-block::

    from django.shortcuts import render
    from django.contrib.auth.decorators import login_required
    from globus_portal_framework.gclients import load_transfer_client
    
    
    @login_required
    def my_view(request, index):
        tc = load_transfer_client(request.user)
        mypaths = tc.operation_ls('ddb59aef-6d04-11e5-ba46-22000b92c6ec', path='/share/godata')
        context = {'mypaths': mypaths}
        return render(request, 'mypaths.html', context)


If your user encounters `my_view` above, the `@login_required` decorator will 
redirect them to the `LOGIN_URL` defined in your `settings.py`

Disabling Links Requiring Login
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to prevent unauthenticated users from even navigating to your views 
in the first place, you can disable links in templates. 

.. code-block::

  <nav>
    <ul class="nav nav-tabs">
      <li class="nav-item">
        <a class="nav-link" href="{% url 'my-landing-page' globus_portal_framework.index %}">About {{project_title}}</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="{% url 'my-projects-page' globus_portal_framework.index %}">Projects</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="{% url 'my-search' globus_portal_framework.index %}">Search</a>
      </li>
      <li class="nav-item">
        <a class="nav-link
          {% if not request.user.is_authenticated %}
          disabled
          {% endif %}
        " href="{% url 'my-files' globus_portal_framework.index %}">View My Files</a>
      </li>
    </ul>
  </nav>


In this example using `Bootstrap <https://getbootstrap.com/docs/4.0/components/navbar/#nav>`_, the "View My Files" link will be disabled.