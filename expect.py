"""Minimal fluent assertion helpers for tests.

This module provides a tiny subset of the `expect`-style API used in tests,
without introducing an external dependency.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class _Expect:
    def __init__(self, actual: Any) -> None:
        self.actual = actual

    def equal(self, expected: Any) -> "_Expect":
        assert self.actual == expected
        return self

    def is_not_equal(self, expected: Any) -> "_Expect":
        assert self.actual != expected
        return self

    def is_not_none(self) -> "_Expect":
        assert self.actual is not None
        return self

    def is_none(self) -> "_Expect":
        assert self.actual is None
        return self

    def to_be_true(self) -> "_Expect":
        assert bool(self.actual) is True
        return self

    def to_be_false(self) -> "_Expect":
        assert bool(self.actual) is False
        return self

    def contains(self, expected_member: Any) -> "_Expect":
        assert expected_member in self.actual
        return self

    def has_keys(self, *keys: str) -> "_Expect":
        assert isinstance(self.actual, Mapping)
        for key in keys:
            assert key in self.actual
        return self

    def is_in(self, container: Sequence[Any]) -> "_Expect":
        assert self.actual in container
        return self

    def to_be_less_than(self, value: float) -> "_Expect":
        assert self.actual < value
        return self


def expect(actual: Any) -> _Expect:
    return _Expect(actual)
