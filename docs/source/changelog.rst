Changelog
=========

Unreleased
----------

* Initial documentation set.
* ``SQLAlchemyDBPromise`` now carries an optional ``error`` and exposes
  ``value`` as ``Result[Exception, M]``, allowing repository operations to
  report arbitrary failures (not just ``NotFoundError``) through the
  promise.
* ``SQLAlchemyWithID`` now stores the domain model directly and accepts it
  as a constructor argument (``SQLAlchemyWithID(model, model_orm)``);
  ``get_model`` returns the stored instance instead of calling
  ``ModelORM.to_model`` on every access.
* ``ModelORM.to_model`` is no longer abstract and is documented to raise
  on failure.
* ``SQLAlchemyRepository.get`` / ``update`` / ``delete`` capture
  ``NotFoundError`` and any exception raised by ``to_model`` and surface
  them on the returned promise instead of raising; failed ``delete`` calls
  leave the record intact.

0.1.0
-----

* Initial project skeleton with message bus, repository, unit of work and
  broker packages.
