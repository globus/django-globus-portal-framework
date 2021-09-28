Django Globus Portal Framework
==============================

.. image:: https://github.com/globus/django-globus-portal-framework/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/globus/django-globus-portal-framework/actions

.. image:: https://img.shields.io/pypi/v/django-globus-portal-framework.svg
    :target: https://pypi.python.org/pypi/django-globus-portal-framework

.. image:: https://img.shields.io/pypi/wheel/django-globus-portal-framework.svg
    :target: https://pypi.python.org/pypi/django-globus-portal-framework

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :alt: License
    :target: https://opensource.org/licenses/Apache-2.0

Globus Portal Framework is a collection of tools for quickly bootstrapping a
portal for Globus Search. Use the guide below to get your portal running with
Globus Auth and your custom search data. After that, you can make your data
more accessible with Globus Transfer, or extend it how you want with your custom
workflow.

Installation
------------

Django Globus Portal Framework is not yet on PyPi, and requires installation through
github. You can install the version you want via tags.

Get the latest features on the main branch:

.. code-block::

  pip install -U -e git+https://github.com/globus/django-globus-portal-framework@main#egg=django-globus-portal-framework

For older stable releases, you can specify the tag:

.. code-block::

  pip install -U -e git+https://github.com/globus/django-globus-portal-framework@v0.3.22#egg=django-globus-portal-framework


Documentation
-------------

Checkout the `docs on S3 here <https://django-globus-portal-framework.s3.us-east-2.amazonaws.com/index.html>`_.

