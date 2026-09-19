from typing import ClassVar

from katharos.types import Result

from hexacore.invariant import InvariantModel, invariant


def test_successful_checks_run_in_declaration_order_for_each_instance() -> None:
    calls: list[tuple[str, InvariantModel]] = []

    class Model(InvariantModel):
        @invariant
        def z_first(self) -> Result[Exception, None]:
            calls.append(("first", self))
            return Result.Success(None)

        @invariant
        def a_second(self) -> Result[Exception, None]:
            calls.append(("second", self))
            return Result.Success(None)

    first = Model()
    second = Model()
    assert [name for name, _ in calls] == ["first", "second", "first", "second"]
    assert all(model is first for _, model in calls[:2])
    assert all(model is second for _, model in calls[2:])


def test_inherited_checks_run_before_subclass_checks() -> None:
    calls: list[str] = []

    class Base(InvariantModel):
        @invariant
        def base_check(self) -> Result[Exception, None]:
            calls.append("base")
            return Result.Success(None)

    class Middle(Base):
        @invariant
        def middle_check(self) -> Result[Exception, None]:
            calls.append("middle")
            return Result.Success(None)

    class Leaf(Middle):
        @invariant
        def leaf_check(self) -> Result[Exception, None]:
            calls.append("leaf")
            return Result.Success(None)

    Leaf()
    assert calls == ["base", "middle", "leaf"]


def test_decorated_override_moves_to_subclass_declaration_order() -> None:
    calls: list[str] = []

    class Base(InvariantModel):
        @invariant
        def overridden(self) -> Result[Exception, None]:
            calls.append("base-overridden")
            return Result.Success(None)

        @invariant
        def retained(self) -> Result[Exception, None]:
            calls.append("retained")
            return Result.Success(None)

    class Child(Base):
        @invariant
        def before(self) -> Result[Exception, None]:
            calls.append("before")
            return Result.Success(None)

        @invariant
        def overridden(self) -> Result[Exception, None]:
            calls.append("child-overridden")
            return Result.Success(None)

        @invariant
        def after(self) -> Result[Exception, None]:
            calls.append("after")
            return Result.Success(None)

    Child()
    assert calls == ["retained", "before", "child-overridden", "after"]
    calls.clear()
    Base()
    assert calls == ["base-overridden", "retained"]


def test_undecorated_override_disables_inherited_check_for_descendants() -> None:
    calls: list[str] = []

    class Base(InvariantModel):
        @invariant
        def check(self) -> Result[Exception, None]:
            calls.append("base")
            return Result.Success(None)

    class Child(Base):
        def check(self) -> Result[Exception, None]:
            calls.append("child")
            return Result.Success(None)

    class Grandchild(Child):
        pass

    model = Grandchild()
    assert calls == []
    assert model.check() == Result.Success(None)
    assert calls == ["child"]


def test_property_override_disables_inherited_check_without_evaluation() -> None:
    class Base(InvariantModel):
        @invariant
        def check(self) -> Result[Exception, None]:
            raise AssertionError("overridden invariant must not run")

    class Child(Base):
        @property
        def check(self) -> str:
            raise AssertionError("property must not be evaluated")

    assert isinstance(Child(), Child)


def test_multiple_inheritance_uses_reverse_mro_and_effective_override() -> None:
    calls: list[str] = []

    class Left(InvariantModel):
        @invariant
        def left_check(self) -> Result[Exception, None]:
            calls.append("left")
            return Result.Success(None)

        @invariant
        def shared(self) -> Result[Exception, None]:
            calls.append("left-shared")
            return Result.Success(None)

    class Right(InvariantModel):
        @invariant
        def shared(self) -> Result[Exception, None]:
            calls.append("right-shared")
            return Result.Success(None)

        @invariant
        def right_check(self) -> Result[Exception, None]:
            calls.append("right")
            return Result.Success(None)

    class Child(Left, Right):
        @invariant
        def child_check(self) -> Result[Exception, None]:
            calls.append("child")
            return Result.Success(None)

    Child()
    assert calls == ["right", "left", "left-shared", "child"]


def test_diamond_inheritance_runs_shared_ancestor_once() -> None:
    calls: list[str] = []

    class Ancestor(InvariantModel):
        @invariant
        def ancestor_check(self) -> Result[Exception, None]:
            calls.append("ancestor")
            return Result.Success(None)

    class Left(Ancestor):
        @invariant
        def left_check(self) -> Result[Exception, None]:
            calls.append("left")
            return Result.Success(None)

    class Right(Ancestor):
        @invariant
        def right_check(self) -> Result[Exception, None]:
            calls.append("right")
            return Result.Success(None)

    class Child(Left, Right):
        @invariant
        def child_check(self) -> Result[Exception, None]:
            calls.append("child")
            return Result.Success(None)

    Child()
    assert calls == ["ancestor", "right", "left", "child"]


def test_unmarked_methods_and_descriptors_are_not_invoked() -> None:
    class ExplodingDescriptor:
        __model_invariant__ = True

        def __get__(self, instance: object, owner: type | None = None) -> object:
            raise AssertionError("descriptor must not be evaluated")

    class Model(InvariantModel):
        descriptor: ClassVar[ExplodingDescriptor] = ExplodingDescriptor()

        def ordinary(self) -> Result[Exception, None]:
            raise AssertionError("ordinary method must not run")

        @property
        def property_value(self) -> str:
            raise AssertionError("property must not be evaluated")

        @staticmethod
        def static_check() -> None:
            raise AssertionError("static method must not run")

        @classmethod
        def class_check(cls) -> None:
            raise AssertionError("class method must not run")

        @staticmethod
        @invariant
        def marked_static(model: InvariantModel) -> Result[Exception, None]:
            raise AssertionError("marked function inside a descriptor must not run")

        @classmethod
        @invariant
        def marked_class(cls) -> Result[Exception, None]:
            raise AssertionError("marked function inside a descriptor must not run")

    assert isinstance(Model(), Model)
