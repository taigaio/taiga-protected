===============
taiga-protected
===============

taiga-protected is a service that implements token validation.

This project is a part of the system. The complete system is integrated by:

- nginx with specific configuration.

- taiga-protected service to validate tokens (this!)

- taiga-contrib-protected plugin, an alternative storage system for taiga-back.

Configuration
=============

The server has 2 configuration options:

- `SECRET_KEY`. This is the shared secret used by the signer.

- `MAX_AGE` (optional). This is the expiration time in seconds.

Options could be set using environment variables or in a `.env` file.

Bug reports, enhancements and support
=====================================

If you **need help to setup Taiga**, want to **talk about some cool enhancemnt** or you have **some questions**, please write us to our [mailing list](http://groups.google.com/d/forum/taigaio).

If you **find a bug** in Taiga you can always report it:

- in [Taiga issues](https://tree.taiga.io/project/taiga/issues).
- send us a mail to support@taiga.io if is a bug related to [tree.taiga.io](https://tree.taiga.io).
- send a mail to security@taiga.io if is a **security bug**.

One of our fellow Taiga developers will search, find and hunt it as soon as possible.

Please, before reporting a bug write down how can we reproduce it, your operating system, your browser and version, and if it's possible, a screenshot. Sometimes it takes less time to fix a bug if the developer knows how to find it and we will solve your problem as fast as possible.

Vendoring
=========

How to update vendored libraries.

.. code::

   pip install -t _vendor -r _vendor/vendor.txt --no-compile --no-deps
   rm -rf _vendor/*.dist-info/

