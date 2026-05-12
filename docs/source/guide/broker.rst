Broker
======

The broker package contains adapters for integrating with external message
brokers. The default implementation targets RabbitMQ via `pika`.

* :class:`hexacore.broker.BaseBrokerConnection` -- the abstract connection
  interface.
* :class:`hexacore.broker.RabbitMQConnection` -- the RabbitMQ adapter.
* :class:`hexacore.broker.EventPublisher` -- publishes events to the broker.
* :class:`hexacore.broker.EventListener` -- consumes events from the broker
  and dispatches them through your application.

See the :doc:`API reference <../api/hexacore/broker/index>` for details.
