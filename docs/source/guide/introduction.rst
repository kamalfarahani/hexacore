Introduction
============

``hexacore`` is a small framework that helps you write Python applications
following the hexagonal (ports-and-adapters) architecture. It does not impose
a particular web framework, ORM or messaging system; instead it provides a
set of focused abstractions that you can compose to keep your domain logic
isolated from infrastructure concerns.

Core concepts
-------------

Commands and events
    Plain data objects -- :class:`~hexacore.command.BaseCommand` and
    :class:`~hexacore.event.BaseEvent` -- that represent intent and facts in
    your domain.

Message bus
    Routes commands and events to registered handlers. See
    :mod:`hexacore.message_bus`.

Repositories
    Abstract collection-like interfaces for aggregates, with a SQLAlchemy
    implementation provided out of the box. See :mod:`hexacore.repository`.

Unit of work
    Coordinates a transactional boundary across one or more repositories.
    See :mod:`hexacore.unit_of_work`.

Broker
    Adapters for publishing and consuming integration events via a message
    broker (RabbitMQ today). See :mod:`hexacore.broker`.

The :doc:`API Reference <../api/hexacore/index>` documents every public
symbol in detail.
