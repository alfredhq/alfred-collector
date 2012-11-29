Alfred Collector
================

.. image:: https://secure.travis-ci.org/alfredhq/alfred-collector.png?branch=develop

Collector receives push fixes from workers and stores them in the database.

Push fixes must be sent as triples::

    [:push_id, :type, :data]

Where:

- ``push_id`` is an ID of the push. It must be of ``int`` type.
- ``type`` is a message type (``'start'``, ``'fix'`` or ``'finish'``, messages
  with other types are ignored).
- ``data`` is ``dict`` with a fix data in case of ``fix`` message, ``None`` in
  case of ``start`` message, or error message in case of ``finish`` message. If
  there is no error, ``None`` must be sent.

You can run a collector using this command::

    $ alfred-collector path/to/the/config.yml

Config example::

    database_uri: "postgresql://localhost/alfred"
    collectors:
      - "tcp://127.0.0.1:7000"
      - "tcp://127.0.0.1:7001"
