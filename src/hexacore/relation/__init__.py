"""Provide base types for collecting and describing relation changes."""

from .base_relation import BaseRelation
from .base_relation_mutation import BaseRelationMutation
from .many_to_many import ManyToMany
from .one_to_many import OneToMany
from .one_to_one import OneToOne

__all__ = [
    "BaseRelation",
    "BaseRelationMutation",
    "ManyToMany",
    "OneToMany",
    "OneToOne",
]
