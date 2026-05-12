Unit of work
============

The unit of work groups one or more repository operations into a single
transactional boundary.

* :class:`hexacore.unit_of_work.BaseUnitOfWork` -- the abstract interface.
* :class:`hexacore.unit_of_work.SQLAlchemyUnitOfWork` -- a SQLAlchemy-backed
  implementation that wraps a ``Session`` in a context manager and exposes
  ``commit`` / ``rollback`` semantics.

See the :doc:`API reference <../api/hexacore/unit_of_work/index>` for details.
