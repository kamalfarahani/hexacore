Repository
==========

Repositories provide a collection-like abstraction for retrieving and
persisting aggregates.

* :class:`hexacore.repository.BaseRepository` -- the abstract interface.
* :class:`hexacore.repository.SQLAlchemyRepository` -- a ready-to-use
  implementation built on top of SQLAlchemy 2.x.

Database promises
-----------------

Repository methods (``add``, ``get``, ``update``, ``delete``) do not return
domain models directly.  Instead they return a
:class:`hexacore.repository.BaseDBPromise` -- a deferred handle to the
persisted entity that may not have a database-assigned ID until the
surrounding transaction is flushed.

The SQLAlchemy adapter returns
:class:`hexacore.repository.sqlalchemy.SQLAlchemyDBPromise` instances which
expose three properties:

``value``
    A ``Result[Exception, M]`` containing either the domain model or any
    exception that occurred (for example :class:`~hexacore.repository.exceptions.NotFoundError`
    when the entity was missing, or any error raised by ``to_model``).

``ready``
    ``True`` once the wrapped entity has a database-assigned ID.  Newly
    added models are not ready until the session is flushed.

``result``
    A ``Result[PromiseNotReadyError, SQLAlchemyWithID[M]]`` exposing the
    full ``WithID`` wrapper, or a failure when the promise is not yet ready.

Error handling
--------------

The SQLAlchemy repository never raises directly from its CRUD methods.
Failures are surfaced through the returned promise:

* Missing records produce a promise whose ``value`` is a
  :class:`~hexacore.repository.exceptions.NotFoundError` failure.
* Exceptions raised by ``ModelORM.to_model`` during ``get`` or ``delete``
  are captured and surfaced as failures on the returned promise; the
  underlying record is left untouched.

The ``ModelORM.to_model`` method is no longer abstract -- subclasses may
override it but are not required to, and it may raise any exception when
conversion fails.

See the :doc:`API reference <../api/hexacore/repository/index>` for details.
