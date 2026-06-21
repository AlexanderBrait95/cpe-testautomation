"""Simulated RADIUS service for headless testing."""
from __future__ import annotations


class SimRADIUSService:
    """In-memory RADIUS user store with PAP authentication."""

    def __init__(self) -> None:
        # username → password
        self._users: dict[str, str] = {}
        # username → attributes
        self._attributes: dict[str, dict[str, str]] = {}

    def add_user(self, username: str, password: str, attributes: dict[str, str] | None = None) -> None:
        self._users[username] = password
        self._attributes[username] = attributes or {}

    def remove_user(self, username: str) -> None:
        self._users.pop(username, None)
        self._attributes.pop(username, None)

    def authenticate(self, username: str, password: str) -> bool:
        stored = self._users.get(username)
        return stored is not None and stored == password

    # Test-helper accessors
    def get_user_attributes(self, username: str) -> dict[str, str]:
        return dict(self._attributes.get(username, {}))

    def has_user(self, username: str) -> bool:
        return username in self._users
