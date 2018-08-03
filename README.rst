===============
taiga-protected
===============

taiga-protected is a service that implements token validation.

This project is a part of the system. The complete system is integrated by:

- nginx with specific configuration.

- taiga-protected service to validate tokens (this!)

- taiga-contrib-protected plugin, an alternative storage system for taiga-back.

Vendoring
=========

How to update vendored libraries.

.. code::

   pip install -t _vendor -r _vendor/vendor.txt --no-compile --no-deps
   rm -rf _vendor/*.dist-info/

