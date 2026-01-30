"""
Tests for LocationCache — the persistent two-file JSON cache with
fuzzy matching and frequency-weighted lookups.

Run:  conda activate fbt && pytest tests/test_location_cache.py -v
"""

import json
import os
import shutil
import tempfile

import pytest

from location_extraction.location_cache import LocationCache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir():
    """Create a fresh temp directory for each test, cleaned up afterwards."""
    d = tempfile.mkdtemp(prefix="loc_cache_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture()
def empty_cache(tmp_dir):
    """A LocationCache initialised with no pre-existing files."""
    return LocationCache(cache_dir=tmp_dir)


@pytest.fixture()
def seeded_cache(tmp_dir):
    """A cache pre-loaded with a handful of realistic entries."""
    cache = LocationCache(cache_dir=tmp_dir)

    # Resolved locations — varying hit counts for frequency tests
    cache.store("swan hill", {
        "lat": -35.338, "lon": 143.55,
        "state": "VIC", "city": "Swan Hill", "type": "regional",
    }, source="location_db")
    # Bump hit_count to 14
    for _ in range(13):
        cache.store("swan hill", {
            "lat": -35.338, "lon": 143.55,
            "state": "VIC", "city": "Swan Hill", "type": "regional",
        }, source="location_db")

    cache.store("orange", {
        "lat": -33.284, "lon": 149.1004,
        "state": "NSW", "city": "Orange", "type": "regional",
    }, source="location_db")
    # Bump to 13
    for _ in range(12):
        cache.store("orange", {
            "lat": -33.284, "lon": 149.1004,
            "state": "NSW", "city": "Orange", "type": "regional",
        }, source="location_db")

    cache.store("swan hill racecourse", {
        "lat": -35.338, "lon": 143.55,
        "state": "VIC", "city": "Swan Hill", "type": "regional",
        "display_name": "Swan Hill Racecourse, Swan Hill, VIC",
    }, source="location_db")

    cache.store("swan hill racing", {
        "lat": -35.338, "lon": 143.55,
        "state": "VIC", "city": "Swan Hill", "type": "regional",
    }, source="location_db")

    # Unresolvable entries
    cache.store_unresolvable("SKYLINE LUGE PHOTOS")
    for _ in range(17):
        cache.store_unresolvable("SKYLINE LUGE PHOTOS")

    cache.store_unresolvable("STRIKE AUSTRALIA PTY L")
    for _ in range(10):
        cache.store_unresolvable("STRIKE AUSTRALIA PTY L")

    cache.store_unresolvable("FH* TIME SAFARIS")
    for _ in range(8):
        cache.store_unresolvable("FH* TIME SAFARIS")

    return cache


@pytest.fixture()
def cache_with_overrides(tmp_dir):
    """A cache that also has an overrides file pre-seeded."""
    # Write overrides JSON first
    overrides = {
        "_meta": {"description": "test overrides", "version": 1},
        "overrides": {
            "skyline luge photos": {
                "lat": -45.0312, "lon": 168.6626,
                "state": "NZ", "city": "Queenstown",
                "country": "New Zealand", "type": "international",
                "display_name": "Skyline Luge, Queenstown, New Zealand",
                "reason": "Skyline Luge is in Queenstown NZ",
            },
            "keukenhof b v": {
                "lat": 52.2697, "lon": 4.5462,
                "state": "NL", "city": "Lisse",
                "country": "Netherlands", "type": "international",
                "display_name": "Keukenhof Gardens, Lisse, Netherlands",
                "reason": "Dutch flower garden",
            },
        },
    }
    with open(os.path.join(tmp_dir, "location_overrides.json"), "w") as f:
        json.dump(overrides, f)

    cache = LocationCache(cache_dir=tmp_dir)

    # Also store skyline as unresolvable in the auto-cache
    for _ in range(18):
        cache.store_unresolvable("SKYLINE LUGE PHOTOS")

    return cache


@pytest.fixture()
def real_data_cache():
    """
    Cache initialised against the real data/ directory.
    Read-only — does NOT save back to disk.
    """
    return LocationCache(cache_dir="data")


# =========================================================================
# 1. Normalisation
# =========================================================================

class TestNormalize:
    def test_lowercase(self):
        assert LocationCache._normalize("SWAN HILL") == "swan hill"

    def test_strip_punctuation(self):
        assert LocationCache._normalize("FH* TIME SAFARIS") == "fh time safaris"

    def test_strip_apostrophes(self):
        assert LocationCache._normalize("MACCA'S SYDNEY") == "macca s sydney"

    def test_collapse_whitespace(self):
        assert LocationCache._normalize("  swan   hill  ") == "swan hill"

    def test_complex_merchant_string(self):
        norm = LocationCache._normalize("KEUKENHOF B.V.")
        assert norm == "keukenhof b v"

    def test_empty_string(self):
        assert LocationCache._normalize("") == ""

    def test_dots_and_dashes(self):
        assert LocationCache._normalize("U.S.A.-based") == "u s a based"


# =========================================================================
# 2. Store & exact lookup
# =========================================================================

class TestStoreAndExactLookup:
    def test_store_and_retrieve(self, empty_cache):
        empty_cache.store("swan hill", {
            "lat": -35.338, "lon": 143.55, "state": "VIC", "type": "regional",
        }, source="location_db")

        data, conf = empty_cache.lookup("swan hill")
        assert data is not None
        assert conf == 100.0
        assert data["lat"] == -35.338
        assert data["state"] == "VIC"
        assert data["resolved"] is True

    def test_case_insensitive_lookup(self, empty_cache):
        empty_cache.store("swan hill", {
            "lat": -35.338, "lon": 143.55, "state": "VIC",
        })
        data, conf = empty_cache.lookup("SWAN HILL")
        assert data is not None
        assert conf == 100.0

    def test_lookup_miss(self, empty_cache):
        data, conf = empty_cache.lookup("nonexistent place")
        assert data is None
        assert conf == 0.0

    def test_empty_string_lookup(self, empty_cache):
        data, conf = empty_cache.lookup("")
        assert data is None
        assert conf == 0.0

    def test_store_increments_hit_count(self, empty_cache):
        for _ in range(5):
            empty_cache.store("dubbo", {"lat": -32.25, "lon": 148.6, "state": "NSW"})
        data, _ = empty_cache.lookup("dubbo")
        assert data["hit_count"] >= 5

    def test_store_preserves_first_seen(self, empty_cache):
        empty_cache.store("dubbo", {"lat": -32.25, "lon": 148.6, "state": "NSW"})
        data1, _ = empty_cache.lookup("dubbo")
        first_seen = data1["first_seen"]

        # Store again — first_seen should NOT change
        empty_cache.store("dubbo", {"lat": -32.25, "lon": 148.6, "state": "NSW"})
        data2, _ = empty_cache.lookup("dubbo")
        assert data2["first_seen"] == first_seen


# =========================================================================
# 3. Unresolvable tracking
# =========================================================================

class TestUnresolvable:
    def test_store_unresolvable(self, empty_cache):
        empty_cache.store_unresolvable("SKYLINE LUGE PHOTOS")
        # Lookup should return (None, -1.0) — known unresolvable sentinel
        data, conf = empty_cache.lookup("SKYLINE LUGE PHOTOS")
        assert data is None
        assert conf == -1.0

    def test_unresolvable_bumps_hit_count(self, empty_cache):
        for _ in range(10):
            empty_cache.store_unresolvable("STRIKE AUSTRALIA PTY L")
        entries = empty_cache._cache["entries"]
        key = LocationCache._normalize("STRIKE AUSTRALIA PTY L")
        assert entries[key]["hit_count"] == 10
        assert entries[key]["resolved"] is False

    def test_unresolvable_appears_in_queue(self, seeded_cache):
        unresolved = seeded_cache.get_unresolved()
        keys = [e["key"] for e in unresolved]
        assert "skyline luge photos" in keys
        assert "strike australia pty l" in keys

    def test_unresolved_sorted_by_frequency(self, seeded_cache):
        unresolved = seeded_cache.get_unresolved()
        hits = [e["hit_count"] for e in unresolved]
        assert hits == sorted(hits, reverse=True), "Unresolved queue must be sorted by hit_count desc"

    def test_unresolvable_not_returned_by_fuzzy_cache(self, empty_cache):
        """Fuzzy cache search should skip resolved=false entries."""
        empty_cache.store_unresolvable("SKYLINE LUGE PHOTOS")
        data, conf = empty_cache.lookup("SKYLINE LUGE PHOTO")  # close but fuzzy
        # Should NOT return the unresolvable entry as a fuzzy match
        assert data is None


# =========================================================================
# 4. Overrides priority
# =========================================================================

class TestOverridesPriority:
    def test_exact_override(self, cache_with_overrides):
        data, conf = cache_with_overrides.lookup("SKYLINE LUGE PHOTOS")
        assert data is not None
        assert conf == 100.0
        assert data["city"] == "Queenstown"
        assert data["type"] == "international"

    def test_override_beats_unresolvable_cache(self, cache_with_overrides):
        """Override must win even though the auto-cache has it as unresolvable."""
        data, conf = cache_with_overrides.lookup("skyline luge photos")
        assert data is not None
        assert data["city"] == "Queenstown"

    def test_fuzzy_override(self, cache_with_overrides):
        """A close-but-not-exact string should still match the override."""
        data, conf = cache_with_overrides.lookup("SKYLINE LUGE PHOTO")
        assert data is not None
        assert conf >= 85.0
        assert data["city"] == "Queenstown"

    def test_keukenhof_override(self, cache_with_overrides):
        data, conf = cache_with_overrides.lookup("KEUKENHOF B.V.")
        assert data is not None
        assert data["city"] == "Lisse"
        assert data["country"] == "Netherlands"

    def test_add_override_programmatic(self, empty_cache):
        empty_cache.add_override("SOME VENUE NZ", {
            "lat": -41.0, "lon": 174.0, "state": "NZ", "city": "Wellington",
            "type": "international",
        }, reason="test override")

        data, conf = empty_cache.lookup("SOME VENUE NZ")
        assert data is not None
        assert conf == 100.0
        assert data["city"] == "Wellington"
        assert data["reason"] == "test override"

    def test_override_excludes_from_unresolved_queue(self, cache_with_overrides):
        """Items with an override should NOT appear in the unresolved queue."""
        unresolved = cache_with_overrides.get_unresolved()
        keys = [e["key"] for e in unresolved]
        assert "skyline luge photos" not in keys


# =========================================================================
# 5. Fuzzy matching
# =========================================================================

class TestFuzzyMatching:
    def test_fuzzy_cache_hit(self, seeded_cache):
        """'SWAN HIL' should fuzzy-match 'swan hill'."""
        data, conf = seeded_cache.lookup("SWAN HIL")
        assert data is not None
        assert conf >= 85.0
        assert data["state"] == "VIC"

    def test_below_threshold_returns_none(self, seeded_cache):
        """A completely unrelated string should not fuzzy match."""
        data, conf = seeded_cache.lookup("XYZZY FOOBAR QUUX")
        assert data is None
        assert conf == 0.0

    def test_fuzzy_uses_token_sort(self, seeded_cache):
        """Token-sort should handle word reordering: 'HILL SWAN' ~ 'swan hill'."""
        data, conf = seeded_cache.lookup("HILL SWAN")
        assert data is not None
        assert conf >= 85.0


# =========================================================================
# 6. Frequency-weighted tiebreaker  (the key innovation)
# =========================================================================

class TestFrequencyWeighting:
    def test_higher_hit_count_wins_fuzzy_tiebreak(self, seeded_cache):
        """
        For input 'SWAN HILL RACE':
        - 'swan hill racecourse' has hit_count=1
        - 'swan hill racing'     has hit_count=1
        - 'swan hill'            has hit_count=14  (highest)
        All score above 85.  The one with most hits should win.
        """
        data, conf = seeded_cache.lookup("SWAN HILL RACE")
        assert data is not None
        assert conf >= 85.0
        # swan hill has 14 hits vs 1 for the others — it should win
        assert data["hit_count"] >= 14

    def test_top_locations_sorted_by_frequency(self, seeded_cache):
        top = seeded_cache.get_top_locations(10)
        hits = [e["hit_count"] for e in top]
        assert hits == sorted(hits, reverse=True)

    def test_top_locations_content(self, seeded_cache):
        """Swan Hill (14) and Orange (13) should be the top two."""
        top = seeded_cache.get_top_locations(2)
        keys = [e["key"] for e in top]
        assert "swan hill" in keys
        assert "orange" in keys

    def test_get_top_locations_respects_n(self, seeded_cache):
        assert len(seeded_cache.get_top_locations(1)) == 1
        assert len(seeded_cache.get_top_locations(100)) <= 100


# =========================================================================
# 7. Stats
# =========================================================================

class TestStats:
    def test_empty_stats(self, empty_cache):
        stats = empty_cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["resolved"] == 0
        assert stats["unresolved"] == 0
        assert stats["total_lookups"] == 0

    def test_stats_after_stores(self, seeded_cache):
        stats = seeded_cache.get_stats()
        assert stats["total_entries"] > 0
        assert stats["resolved"] >= 2  # swan hill + orange + others
        assert stats["unresolved"] >= 3  # skyline, strike, fh*
        assert stats["sources"]["location_db"] >= 2

    def test_lookup_increments_total_lookups(self, empty_cache):
        empty_cache.store("dubbo", {"lat": -32.25, "lon": 148.6, "state": "NSW"})
        empty_cache.lookup("dubbo")
        empty_cache.lookup("dubbo")
        empty_cache.lookup("missing")
        stats = empty_cache.get_stats()
        assert stats["total_lookups"] == 3


# =========================================================================
# 8. Persistence (save & reload)
# =========================================================================

class TestPersistence:
    def test_save_creates_files(self, empty_cache, tmp_dir):
        empty_cache.store("orange", {"lat": -33.28, "lon": 149.1, "state": "NSW"})
        empty_cache.save()

        assert os.path.isfile(os.path.join(tmp_dir, "location_cache.json"))
        assert os.path.isfile(os.path.join(tmp_dir, "location_overrides.json"))

    def test_round_trip(self, tmp_dir):
        """Store data, save, create a new cache from same dir — data persists."""
        c1 = LocationCache(cache_dir=tmp_dir)
        c1.store("swan hill", {"lat": -35.338, "lon": 143.55, "state": "VIC"})
        c1.store_unresolvable("UNKNOWN THING")
        c1.add_override("special place", {
            "lat": 1.0, "lon": 2.0, "city": "Test", "state": "XX",
        }, reason="test")
        c1.save()

        # Reload
        c2 = LocationCache(cache_dir=tmp_dir)
        data, conf = c2.lookup("swan hill")
        assert data is not None
        assert data["state"] == "VIC"

        data2, conf2 = c2.lookup("special place")
        assert data2 is not None
        assert data2["city"] == "Test"

        unresolved = c2.get_unresolved()
        keys = [e["key"] for e in unresolved]
        assert "unknown thing" in keys

    def test_saved_json_is_valid(self, empty_cache, tmp_dir):
        empty_cache.store("test", {"lat": 0, "lon": 0, "state": "XX"})
        empty_cache.save()

        with open(os.path.join(tmp_dir, "location_cache.json")) as f:
            data = json.load(f)
        assert "_meta" in data
        assert "entries" in data
        assert "test" in data["entries"]

    def test_corrupted_json_falls_back_to_empty(self, tmp_dir):
        """If the JSON file is corrupted, cache should start fresh."""
        with open(os.path.join(tmp_dir, "location_cache.json"), "w") as f:
            f.write("{BROKEN JSON!!!")
        cache = LocationCache(cache_dir=tmp_dir)
        stats = cache.get_stats()
        assert stats["total_entries"] == 0

    def test_missing_files_starts_empty(self, tmp_dir):
        cache = LocationCache(cache_dir=tmp_dir)
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["overrides"] == 0


# =========================================================================
# 9. Integration with real data/location_overrides.json
# =========================================================================

class TestRealDataFiles:
    """Tests against the actual data/ directory files (read-only)."""

    def test_real_overrides_load(self, real_data_cache):
        stats = real_data_cache.get_stats()
        assert stats["overrides"] >= 2, "Should have at least 2 overrides (skyline, keukenhof)"

    def test_real_skyline_override(self, real_data_cache):
        data, conf = real_data_cache.lookup("SKYLINE LUGE PHOTOS")
        assert data is not None
        assert data["city"] == "Queenstown"

    def test_real_keukenhof_override(self, real_data_cache):
        data, conf = real_data_cache.lookup("KEUKENHOF B.V.")
        assert data is not None
        assert data["city"] == "Lisse"

    def test_real_fuzzy_skyline(self, real_data_cache):
        """Fuzzy match on the real overrides file."""
        data, conf = real_data_cache.lookup("SKYLINE LUGE PHOTO")
        assert data is not None
        assert conf >= 85.0
        assert data["city"] == "Queenstown"


# =========================================================================
# 10. Lookup order integration
# =========================================================================

class TestLookupOrder:
    def test_override_wins_over_cache(self, tmp_dir):
        """If both cache and overrides have an entry, override wins."""
        cache = LocationCache(cache_dir=tmp_dir)

        # Store in cache as resolved (wrong data)
        cache.store("test place", {
            "lat": 0.0, "lon": 0.0, "state": "WRONG", "city": "Wrong City",
        })

        # Add override with correct data
        cache.add_override("test place", {
            "lat": 1.0, "lon": 1.0, "state": "RIGHT", "city": "Right City",
        })

        data, conf = cache.lookup("test place")
        assert data["city"] == "Right City"
        assert data["state"] == "RIGHT"

    def test_cache_hit_increments_count(self, seeded_cache):
        """Each exact cache lookup should increment hit_count."""
        _, _ = seeded_cache.lookup("orange")
        _, _ = seeded_cache.lookup("orange")
        entry = seeded_cache._cache["entries"]["orange"]
        # Original 13 stores + 2 lookups
        assert entry["hit_count"] >= 15

    def test_unresolvable_blocks_further_lookup(self, empty_cache):
        """
        Once stored as unresolvable, lookup returns (None, -1.0)
        — sentinel tells the caller to skip DB and API re-queries.
        """
        empty_cache.store_unresolvable("GIBBERISH TEXT 123")
        data, conf = empty_cache.lookup("GIBBERISH TEXT 123")
        assert data is None
        assert conf == -1.0


# =========================================================================
# 11. Edge cases
# =========================================================================

class TestEdgeCases:
    def test_store_empty_string_is_noop(self, empty_cache):
        empty_cache.store("", {"lat": 0, "lon": 0})
        assert empty_cache.get_stats()["total_entries"] == 0

    def test_store_unresolvable_empty_string_is_noop(self, empty_cache):
        empty_cache.store_unresolvable("")
        assert empty_cache.get_stats()["total_entries"] == 0

    def test_add_override_empty_string_is_noop(self, empty_cache):
        empty_cache.add_override("", {"lat": 0, "lon": 0})
        assert empty_cache.get_stats()["overrides"] == 0

    def test_unicode_text(self, empty_cache):
        empty_cache.store("café münchen", {
            "lat": 48.1351, "lon": 11.582, "state": "DE", "city": "München",
        })
        data, _ = empty_cache.lookup("café münchen")
        assert data is not None
        assert data["city"] == "München"

    def test_many_entries_performance(self, empty_cache):
        """Store 500 entries and verify lookup still works."""
        for i in range(500):
            empty_cache.store(f"location {i}", {
                "lat": -33.0 + i * 0.01, "lon": 151.0 + i * 0.01,
                "state": "NSW",
            })
        data, conf = empty_cache.lookup("location 250")
        assert data is not None
        assert conf == 100.0

    def test_threshold_boundary(self, tmp_dir):
        """Custom threshold should be respected."""
        cache = LocationCache(cache_dir=tmp_dir, fuzzy_threshold=95)
        cache.store("swan hill racecourse", {
            "lat": -35.338, "lon": 143.55, "state": "VIC",
        })
        # With threshold=95, 'SWAN HILL RACE' may not match (depends on score)
        data, conf = cache.lookup("SWAN HILL RACE")
        if data is not None:
            assert conf >= 95.0
