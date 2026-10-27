from typing import Any, TypeVar, get_args

from katharos.types import ImmutableList
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

T_co = TypeVar("T_co", covariant=True)


class PydanticImmutableList(ImmutableList[T_co]):
    """A Pydantic-compatible immutable list type."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Build a schema that validates immutable lists and serializes them as lists.

        Args:
            source_type: The annotated type, optionally parameterized by item type.
            handler: The handler used to generate the item validation schema.

        Returns:
            A schema that validates items against the declared type, constructs an
            immutable list, and serializes it as a list. Unparameterized lists
            accept items of any type.
        """
        args = get_args(source_type)
        if args:
            item_type = args[0]
            item_schema = handler.generate_schema(item_type)
        else:
            item_schema = core_schema.any_schema()

        return core_schema.no_info_after_validator_function(
            lambda x: ImmutableList(x) if not isinstance(x, ImmutableList) else x,
            core_schema.list_schema(item_schema),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: list(x), return_schema=core_schema.list_schema(item_schema)
            ),
        )
