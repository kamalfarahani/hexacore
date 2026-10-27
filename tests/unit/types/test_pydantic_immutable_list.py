import json
from typing import Any

import pytest
from katharos.types import ImmutableList
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.json_schema import JsonSchemaMode

from hexacore.types import PydanticImmutableList


@pytest.mark.parametrize(
    "values",
    [["1", 2], ("1", 2), ImmutableList(["1", 2]), PydanticImmutableList(["1", 2])],
    ids=["list", "tuple", "immutable-list", "pydantic-immutable-list"],
)
def test_validates_and_coerces_items(values: Any) -> None:
    result = TypeAdapter(PydanticImmutableList[int]).validate_python(values)

    assert isinstance(result, ImmutableList)
    assert list(result) == [1, 2]


def test_accepts_empty_list() -> None:
    result = TypeAdapter(PydanticImmutableList[int]).validate_python([])

    assert isinstance(result, ImmutableList)
    assert list(result) == []


def test_unparameterized_list_preserves_mixed_items() -> None:
    marker = object()
    values = [1, "two", None, {"three": 3}, marker]
    adapter = TypeAdapter(PydanticImmutableList)

    result = adapter.validate_python(values)

    assert isinstance(result, ImmutableList)
    assert list(result) == values
    assert result[-1] is marker
    assert adapter.dump_python(result) == values


@pytest.mark.parametrize("value", [None, 1, "123", {"value": 1}])
def test_rejects_non_list_input(value: Any) -> None:
    with pytest.raises(ValidationError) as caught:
        TypeAdapter(PydanticImmutableList[int]).validate_python(value)

    error = caught.value.errors()[0]
    assert error["type"] == "list_type"
    assert error["loc"] == ()


def test_rejects_invalid_item_with_index() -> None:
    with pytest.raises(ValidationError) as caught:
        TypeAdapter(PydanticImmutableList[int]).validate_python([1, "invalid"])

    error = caught.value.errors()[0]
    assert error["type"] == "int_parsing"
    assert error["loc"] == (1,)


def test_json_validation_and_serialization_round_trip() -> None:
    adapter = TypeAdapter(PydanticImmutableList[int])

    result = adapter.validate_json('["1", 2]')

    assert isinstance(result, ImmutableList)
    assert list(result) == [1, 2]
    assert adapter.dump_python(result) == [1, 2]
    assert adapter.dump_python(result, mode="json") == [1, 2]
    serialized = adapter.dump_json(result)
    assert json.loads(serialized) == [1, 2]
    assert adapter.validate_json(serialized) == result


def test_model_field_validates_and_serializes_nested_models() -> None:
    class Item(BaseModel):
        value: int

    class Model(BaseModel):
        items: PydanticImmutableList[Item]

    model = Model.model_validate({"items": [{"value": "1"}]})

    assert isinstance(model.items, ImmutableList)
    assert model.items[0] == Item(value=1)
    expected = {"items": [{"value": 1}]}
    assert model.model_dump() == expected
    assert json.loads(model.model_dump_json()) == expected
    assert Model.model_validate_json(model.model_dump_json()) == model

    with pytest.raises(ValidationError) as caught:
        Model.model_validate({"items": [{"value": "invalid"}]})
    assert caught.value.errors()[0]["loc"] == ("items", 0, "value")


@pytest.mark.parametrize("mode", ["validation", "serialization"])
def test_json_schema_describes_array_and_item_type(mode: JsonSchemaMode) -> None:
    typed_schema = TypeAdapter(PydanticImmutableList[int]).json_schema(mode=mode)
    untyped_schema = TypeAdapter(PydanticImmutableList).json_schema(mode=mode)

    assert typed_schema == {"type": "array", "items": {"type": "integer"}}
    assert untyped_schema == {"type": "array", "items": {}}


def test_validated_list_is_independent_of_mutable_input() -> None:
    values = [1, 2]
    result = TypeAdapter(PydanticImmutableList[int]).validate_python(values)

    values.append(3)

    assert list(result) == [1, 2]
    with pytest.raises(TypeError):
        result[0] = 3  # type: ignore[index]
