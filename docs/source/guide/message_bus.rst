Message bus
===========

The message bus routes :class:`~hexacore.command.BaseCommand` and
:class:`~hexacore.event.BaseEvent` instances to registered handlers.

Key types:

* :class:`hexacore.message_bus.BaseMessageBus` -- the abstract bus interface.
* Handler registry helpers in :mod:`hexacore.message_bus.registry`.
* Handler base classes in :mod:`hexacore.message_bus.handler`.

Refer to the :doc:`API reference <../api/hexacore/message_bus/index>` for the
full list of methods and signatures.
