from abc import ABC
from typing import Self

from .base_relation_command import BaseRelationCommand


class BaseRelation(ABC):
    _commands: list[BaseRelationCommand]

    def __init__(self) -> None:
        self._commands = []

    def add_command(self, cmd: BaseRelationCommand) -> None:
        self._commands.append(cmd)

    @property
    def commands(self) -> list[BaseRelationCommand]:
        return self._commands

    def __enter__(self) -> Self:
        self._commands = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
