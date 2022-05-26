Local Credentials
=================

For simplicity, the tutorial has you adding secret credentials directly
to a `settings.py` file. This isn't ideal if using version control to
track general settings. A common workaround is to keep a ``local_settings.py``
in the same directory not tracked by git, and importing them into your
main ``settings.py`` file at the very bottom.

Example ``local_settings.py`` file:

.. code-block::

    # local_settings.py
    SOCIAL_AUTH_GLOBUS_KEY = '<YOUR APP CLIENT ID>'
    SOCIAL_AUTH_GLOBUS_SECRET = '<YOUR APP SECRET>'
    DEBUG = True

Then, at the bottom of ``settings.py``:

.. code-block::

  # Override any settings here if a local_settings.py file exists
  try:
      from .local_settings import *  # noqa
  except ImportError:
      pass

Your normal settings.py file can now be safely tracked within version control.
