"""Simulated file server for headless testing."""
from __future__ import annotations


class SimFileServer:
    """In-memory file store with URL generation."""

    def __init__(self, base_url: str = "http://sim-fileserver.local") -> None:
        self.base_url = base_url
        self._files: dict[str, bytes] = {}

    def put_file(self, filename: str, content: bytes) -> str:
        self._files[filename] = content
        return self.get_url(filename)

    def delete_file(self, filename: str) -> None:
        self._files.pop(filename, None)

    def get_url(self, filename: str) -> str:
        return f"{self.base_url}/{filename}"

    # Test-helper accessors
    def has_file(self, filename: str) -> bool:
        return filename in self._files

    def get_content(self, filename: str) -> bytes | None:
        return self._files.get(filename)

    def list_files(self) -> list[str]:
        return list(self._files.keys())
