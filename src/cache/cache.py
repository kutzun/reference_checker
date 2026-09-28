"""
Verification result cache.

Stores and retrieves verification data locally.
"""

import json
from pathlib import Path


class VerificationCache:
    """
    Simple JSON-based cache.
    """

    def __init__(
        self,
        cache_path: Path,
    ):
        """
        Initialize cache.

        Args:
            cache_path:
                Location of cache JSON file.
        """

        self.cache_path = cache_path

    def _load(
        self,
    ) -> dict:
        """
        Load cache contents.

        Returns:
            Cache dictionary.
        """

        if not self.cache_path.exists():
            return {}

        with self.cache_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _save(
        self,
        data: dict,
    ) -> None:
        """
        Save cache contents.
        """

        self.cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.cache_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def get(
        self,
        key: str,
    ) -> dict | None:
        """
        Retrieve cached value.

        Args:
            key:
                Cache identifier.

        Returns:
            Cached data or None.
        """

        data = self._load()

        return data.get(key)

    def set(
        self,
        key: str,
        value: dict,
    ) -> None:
        """
        Store value in cache.

        Args:
            key:
                Cache identifier.

            value:
                Data to store.
        """

        data = self._load()

        data[key] = value

        self._save(data)
