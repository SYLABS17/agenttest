"""Caching utilities for query results."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any
import hashlib

from cachetools import TTLCache
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """A cached query result."""

    query_hash: str
    result: Any
    created_at: datetime
    hit_count: int = 0


class QueryCache:
    """
    TTL-based cache for query results.

    Caches:
    - Translation results (keyed by query + source language)
    - Search results (keyed by query + filters)
    - Generated responses (keyed by full context)
    """

    def __init__(
        self,
        max_size: int = 10000,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize query cache.

        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live in seconds
        """
        self.settings = get_settings()
        self._cache = TTLCache(
            maxsize=max_size,
            ttl=ttl_seconds or self.settings.cache_ttl_seconds,
        )
        self._hits = 0
        self._misses = 0

    def _compute_key(self, *args) -> str:
        """Compute cache key from arguments."""
        key_str = "|".join(str(arg) for arg in args)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def get(self, *args) -> Optional[Any]:
        """
        Get cached result.

        Args:
            *args: Key components

        Returns:
            Cached result if found, None otherwise
        """
        key = self._compute_key(*args)
        result = self._cache.get(key)

        if result is not None:
            self._hits += 1
            logger.debug("cache_hit", key=key[:8])
            return result

        self._misses += 1
        return None

    def set(self, value: Any, *args) -> None:
        """
        Cache a result.

        Args:
            value: Value to cache
            *args: Key components
        """
        key = self._compute_key(*args)
        self._cache[key] = value
        logger.debug("cache_set", key=key[:8])

    def invalidate(self, *args) -> bool:
        """
        Invalidate a cache entry.

        Args:
            *args: Key components

        Returns:
            True if entry was found and removed
        """
        key = self._compute_key(*args)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("cache_cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._cache.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self._cache.ttl,
        }


class TranslationCache(QueryCache):
    """Specialized cache for translation results."""

    def get_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> Optional[str]:
        """Get cached translation."""
        return self.get(text, source_lang, target_lang)

    def set_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translated: str,
    ) -> None:
        """Cache translation result."""
        self.set(translated, text, source_lang, target_lang)


class SearchCache(QueryCache):
    """Specialized cache for search results."""

    def get_search_results(
        self,
        query: str,
        index: str,
        filters_hash: str,
    ) -> Optional[list]:
        """Get cached search results."""
        return self.get(query, index, filters_hash)

    def set_search_results(
        self,
        query: str,
        index: str,
        filters_hash: str,
        results: list,
    ) -> None:
        """Cache search results."""
        self.set(results, query, index, filters_hash)
