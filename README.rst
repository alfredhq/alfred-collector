Alfred Collector
================

Collector receives report fixes from workers and stores them in the database.

Report fixes must be sent as triples::

    [:report_id, :type, :data]

Where:

- ``report_id`` is an ID of the report. It must be of ``int`` type.
- ``type`` is a message type (``'fix'`` or ``'finish'``, messages with other
  types are ignored).
- ``data`` is ``dict`` with a fix data in case of ``fix`` message, or error
  message in case of ``finish`` message. If there is no error, ``None`` must
  be sent.

You can run a collector using this command::

    $ alfred-collector path/to/the/config.yml

Config example::

    database_uri: "postgresql://localhost/alfred"
    collectors:
      - "tcp://127.0.0.1:7000"
      - "tcp://127.0.0.1:7001"
