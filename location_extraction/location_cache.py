"""
Persistent location cache with fuzzy matching and frequency tracking.

Two-file JSON system:
  - data/location_cache.json   : auto-populated from lookups (system writes)
  - data/location_overrides.json : human corrections (user writes, always wins)

Lookup order:
  1. Overrides  (exact -> fuzzy)
  2. Cache      (exact -> fuzzy, frequency-weighted)
  3. Fall through to caller (location_db / Nominatim / etc.)
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process


class LocationCache:
    """Persistent location cache with fuzzy matching and frequency-weighted lookups."""

    def __init__(self, cache_dir: str = "data", fuzzy_threshold: int = 85):
        self.cache_dir = cache_dir
        self.fuzzy_threshold = fuzzy_threshold

        self._cache_path = os.path.join(cache_dir, "location_cache.json")
        self._overrides_path = os.path.join(cache_dir, "location_overrides.json")

        self._cache = self._load_cache()
        self._overrides = self._load_overrides()

        # Pre-build key lists for rapidfuzz
        self._rebuild_keys()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, strip apostrophes/punctuation, collapse whitespace."""
        text = text.lower().strip()
        text = re.sub(r"['\"\-\.\,\*]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _rebuild_keys(self) -> None:
        """Rebuild key lists used by rapidfuzz after any mutation."""
        self._cache_keys = list(self._cache.get("entries", {}).keys())
        self._override_keys = list(self._overrides.get("overrides", {}).keys())

    def _load_cache(self) -> dict:
        if os.path.exists(self._cache_path):
            try:
                with open(self._cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "_meta": {
                "version": 1,
                "total_entries": 0,
                "total_lookups": 0,
            },
            "entries": {},
        }

    def _load_overrides(self) -> dict:
        if os.path.exists(self._overrides_path):
            try:
                with open(self._overrides_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "_meta": {
                "description": (
                    "Manual corrections - these ALWAYS override the auto-cache. "
                    "Edit this file to fix wrong locations."
                ),
                "version": 1,
            },
            "overrides": {},
        }

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _touch_hit(self, entry: dict) -> None:
        """Increment hit_count and update last_seen."""
        entry["hit_count"] = entry.get("hit_count", 0) + 1
        entry["last_seen"] = self._now_iso()

    def _increment_lookups(self) -> None:
        self._cache["_meta"]["total_lookups"] = (
            self._cache["_meta"].get("total_lookups", 0) + 1
        )

    # ------------------------------------------------------------------
    # Fuzzy helpers
    # ------------------------------------------------------------------
    def _fuzzy_search_overrides(self, key: str) -> Tuple[Optional[dict], float]:
        """Fuzzy match against override keys. Returns (data, score) or (None, 0)."""
        if not self._override_keys:
            return None, 0.0
        results = process.extract(
            key,  # positional, not query=
            self._override_keys,  # positional, not choices=
            scorer=fuzz.token_sort_ratio,
            limit=5,
        )
        for match_key, score, _ in results:
            if score >= self.fuzzy_threshold:
                entry = self._overrides["overrides"][match_key]
                return entry, score
        return None, 0.0

    def _fuzzy_search_cache(self, key: str) -> Tuple[Optional[dict], float]:
        """
        Fuzzy match against cache keys with frequency-weighted tiebreaker.
        Among candidates above threshold, pick the one with highest hit_count.
        Returns (data, score) or (None, 0).
        """
        if not self._cache_keys:
            return None, 0.0
        results = process.extract(
            key,  # positional, not query=
            self._cache_keys,  # positional, not choices=
            scorer=fuzz.token_sort_ratio,
            limit=10,
        )
        # Filter to above-threshold and resolved entries
        candidates = []
        for match_key, score, _ in results:
            if score < self.fuzzy_threshold:
                continue
            entry = self._cache["entries"][match_key]
            if not entry.get("resolved", False):
                continue
            candidates.append((match_key, score, entry))

        if not candidates:
            return None, 0.0

        # Frequency-weighted: among candidates, pick highest hit_count
        # (secondary sort by score for true ties)
        candidates.sort(key=lambda c: (c[2].get("hit_count", 0), c[1]), reverse=True)
        best_key, best_score, best_entry = candidates[0]
        self._touch_hit(best_entry)
        return best_entry, best_score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lookup(self, raw_text: str) -> Tuple[Optional[dict], float]:
        """
        Look up a location string in overrides then cache.

        Returns:
            (data_dict, confidence) — resolved hit with lat/lon/state/etc.
            (None, 0.0)  — not found in any source.
            (None, -1.0) — known unresolvable (caller should skip geocoding).

        Lookup order:
            1. Exact override
            2. Fuzzy override (token_sort_ratio >= threshold)
            3. Exact cache (only if resolved=True; -1.0 if resolved=False)
            4. Fuzzy cache (frequency-weighted, only resolved entries)
            5. No match -> (None, 0.0)
        """
        self._increment_lookups()
        key = self._normalize(raw_text)
        if not key:
            return None, 0.0

        # 1. Exact override
        overrides = self._overrides.get("overrides", {})
        if key in overrides:
            return dict(overrides[key]), 100.0

        # 2. Fuzzy override
        ov_data, ov_score = self._fuzzy_search_overrides(key)
        if ov_data is not None:
            return dict(ov_data), ov_score

        # 3. Exact cache
        entries = self._cache.get("entries", {})
        if key in entries:
            entry = entries[key]
            self._touch_hit(entry)
            if entry.get("resolved", False):
                return dict(entry), 100.0
            # Known unresolvable — sentinel -1.0 tells caller to skip
            return None, -1.0

        # 4. Fuzzy cache (frequency-weighted)
        cache_data, cache_score = self._fuzzy_search_cache(key)
        if cache_data is not None:
            return dict(cache_data), cache_score

        # 5. No match
        return None, 0.0

    def store(self, raw_text: str, data: dict, source: str = "auto") -> None:
        """Store a resolved location in the cache."""
        key = self._normalize(raw_text)
        if not key:
            return
        now = self._now_iso()
        entries = self._cache.setdefault("entries", {})
        existing = entries.get(key)

        entry = {
            "resolved": True,
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "state": data.get("state", ""),
            "city": data.get("city", ""),
            "type": data.get("type", ""),
            "display_name": data.get("display_name", ""),
            "source": source,
            "confidence": data.get("confidence", 0.9),
            "hit_count": (existing.get("hit_count", 0) + 1) if existing else 1,
            "first_seen": existing.get("first_seen", now) if existing else now,
            "last_seen": now,
        }
        entries[key] = entry
        self._cache["_meta"]["total_entries"] = len(entries)
        self._rebuild_keys()

    def store_unresolvable(self, raw_text: str) -> None:
        """Store an entry as unresolvable (avoids re-querying next run)."""
        key = self._normalize(raw_text)
        if not key:
            return
        now = self._now_iso()
        entries = self._cache.setdefault("entries", {})
        existing = entries.get(key)

        if existing:
            # Already exists — just bump hit count
            self._touch_hit(existing)
        else:
            entries[key] = {
                "resolved": False,
                "hit_count": 1,
                "first_seen": now,
                "last_seen": now,
            }
        self._cache["_meta"]["total_entries"] = len(entries)
        self._rebuild_keys()

    def add_override(self, raw_text: str, data: dict, reason: str = "") -> None:
        """Add or update an override entry programmatically."""
        key = self._normalize(raw_text)
        if not key:
            return
        entry = dict(data)
        if reason:
            entry["reason"] = reason
        self._overrides.setdefault("overrides", {})[key] = entry
        self._rebuild_keys()

    def get_stats(self) -> dict:
        """Return summary statistics about the cache."""
        entries = self._cache.get("entries", {})
        resolved = [e for e in entries.values() if e.get("resolved")]
        unresolved = [e for e in entries.values() if not e.get("resolved")]

        # Source breakdown
        sources: Dict[str, int] = {}
        for e in resolved:
            src = e.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1

        return {
            "total_entries": len(entries),
            "resolved": len(resolved),
            "unresolved": len(unresolved),
            "total_lookups": self._cache["_meta"].get("total_lookups", 0),
            "overrides": len(self._overrides.get("overrides", {})),
            "sources": sources,
        }

    def get_top_locations(self, n: int = 20) -> List[dict]:
        """Top N resolved cache entries sorted by hit_count descending."""
        entries = self._cache.get("entries", {})
        resolved = [
            {"key": k, **v}
            for k, v in entries.items()
            if v.get("resolved")
        ]
        resolved.sort(key=lambda e: e.get("hit_count", 0), reverse=True)
        return resolved[:n]

    def get_unresolved(self) -> List[dict]:
        """All unresolvable entries sorted by hit_count descending (user review queue)."""
        entries = self._cache.get("entries", {})
        overrides = self._overrides.get("overrides", {})
        unresolved = [
            {"key": k, **v}
            for k, v in entries.items()
            if not v.get("resolved") and k not in overrides
        ]
        unresolved.sort(key=lambda e: e.get("hit_count", 0), reverse=True)
        return unresolved

    def save(self) -> None:
        """Persist both JSON files to disk (pretty-printed, human-readable)."""
        os.makedirs(self.cache_dir, exist_ok=True)

        # Update meta counts before saving
        self._cache["_meta"]["total_entries"] = len(
            self._cache.get("entries", {})
        )

        with open(self._cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, ensure_ascii=False)

        with open(self._overrides_path, "w", encoding="utf-8") as f:
            json.dump(self._overrides, f, indent=2, ensure_ascii=False)