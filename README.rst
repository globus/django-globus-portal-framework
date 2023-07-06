Django Globus Portal Framework
==============================

.. image:: https://zenodo.org/badge/118486682.svg
   :target: https://zenodo.org/badge/latestdoi/118486682

.. image:: https://github.com/globus/django-globus-portal-framework/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/globus/django-globus-portal-framework/actions

.. image:: https://img.shields.io/pypi/v/django-globus-portal-framework.svg
    :target: https://pypi.python.org/pypi/django-globus-portal-framework

.. image:: https://img.shields.io/pypi/wheel/django-globus-portal-framework.svg
    :target: https://pypi.python.org/pypi/django-globus-portal-framework

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :alt: License
    :target: https://opensource.org/licenses/Apache-2.0

The Django Globus Portal Framework is a collection of tools that enable you to rapidly create an easily accessible portal for your data. Globus provides robust Auth and Search services, both powerful tools to help manage who has access to your data and metadata. Tailoring your portal to your data can be done simply by modifying existing bulit-in Bootstrap templates, allowing many levels of customization to suit the required needs.

Please head to our `Read The Docs page <https://django-globus-portal-framework.readthedocs.io/en/stable/>`_ for installation and usage instructions. If you're just getting started, here is how we recommend you begin:

* Use of this framework requires an account you can use to log in to the Globus Web App. There are many ways to sign in to Globus, including Google and ORCID iD.
* Once signed in to Globus, head to https://app.globus.org/settings/developers and create a project and application to generate a key and secret. You will most likely want "Register a portal, science gateway, or other application".
* The Read-the-Docs link above will cover basic operations for starting a portal. For extended documentation about the Globus Search service, please see the `Globus Search API Documentation <https://docs.globus.org/api/search/>`_

Installation
------------

You can install Django Globus Portal Framework using Pip:

.. code-block::

  pip install django-globus-portal-framework

For our latest development version, you can install the pre-release

.. code-block::

  pip install -U --pre django-globus-portal-framework


See the `Read The Docs page <https://django-globus-portal-framework.readthedocs.io/en/stable/>`_.

Issues
------

All features are currently tracked internally by Shortcut.

If you encounter a bug or would like to request a feature, please open a Github Issue.