"""
Ensemble Location Extraction Strategy

Combines multiple extraction strategies with intelligent fallbacks to maximize
extraction accuracy while maintaining performance. Uses a tiered approach:

Tier 1 (Fast & Precise): Aho-Corasick automaton for exact matches
Tier 2 (Pattern-Based): Gazetteer Regex for pattern matching
Tier 3 (Semantic NER): spaCy NER for context-aware entity extraction
Tier 4 (Fuzzy Matching): Phonetic matching for typos/misspellings
Tier 5 (Vector Space): TF-IDF similarity for complex descriptions

The strategy returns the union of matches from all tiers, with confidence
scoring based on which tier(s) found each location.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from .aho_corasick_strategy import AhoCorasickStrategy
from ..base import BaseModel, PrivateAttr
from ... import CountryDetector, GazetteerRegexStrategy, PhoneticGazetteerStrategy, SklearnBoWStrategy, \
    SklearnTfidfStrategy, \
    SpacyNerStrategy

try:
    from pydantic import ConfigDict
except Exception:
    ConfigDict = dict  # type: ignore


class EnsembleExtractionStrategy(BaseModel):  # type: ignore[misc]
    """
    Ensemble strategy combining multiple extraction approaches with intelligent
    fallback logic for maximum recall and precision.

    Features:
    - Tiered extraction: fast methods first, expensive methods as fallback
    - Confidence scoring: tracks which methods found each location
    - Deduplication: normalizes and merges results from all strategies
    - Configurable: enable/disable individual strategies
    - Performance-aware: caches strategy instances and results

    Usage:
        from location_extraction import AUSTRALIAN_LOCATIONS

        strategy = EnsembleExtractionStrategy(
            locations_db=AUSTRALIAN_LOCATIONS,
            enable_aho_corasick=True,
            enable_regex=True,
            enable_spacy=True,
            enable_phonetic=True,
            enable_tfidf=False,  # Expensive, disable by default
        )

        locations = strategy.extract("Meeting in Sydney CBD")
        # Returns: ['sydney']

        # Get detailed results with confidence
        results = strategy.extract_with_confidence("Meeting in Sydny")
        # Returns: [{'location': 'sydney', 'confidence': 0.85, 'sources': ['phonetic']}]
    """

    locations_db: Dict[str, Dict]

    # Strategy enable flags
    enable_aho_corasick: bool = True
    enable_regex: bool = True
    enable_spacy: bool = True
    enable_phonetic: bool = True
    enable_tfidf: bool = False  # Expensive, disabled by default
    enable_bow: bool = False  # Alternative to TF-IDF

    # spaCy configuration
    spacy_model: str = "en_core_web_sm"
    spacy_models_preference: Optional[List[str]] = None

    # Phonetic configuration
    phonetic_min_token_match_ratio: float = 0.5

    # TF-IDF / BoW configuration
    vector_ngram_range: Tuple[int, int] = (1, 3)
    vector_min_df: int = 1
    vector_max_df: float = 0.9
    vector_max_features: Optional[int] = 5000
    vector_threshold: float = 0.2

    # Ensemble behavior
    min_strategies_for_high_confidence: int = 2
    fallback_on_empty: bool = True  # Try more strategies if fast ones find nothing

    # Allow arbitrary types for strategy instances
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Private attributes for lazy-loaded strategies
    _aho_corasick: Optional[Any] = PrivateAttr(default=None)
    _regex: Optional[Any] = PrivateAttr(default=None)
    _spacy: Optional[Any] = PrivateAttr(default=None)
    _phonetic: Optional[Any] = PrivateAttr(default=None)
    _tfidf: Optional[Any] = PrivateAttr(default=None)
    _bow: Optional[Any] = PrivateAttr(default=None)
    _country_detector: Optional[Any] = PrivateAttr(default=None)
    _initialized: bool = PrivateAttr(default=False)
    _db_keys: Optional[Set[str]] = PrivateAttr(default=None)
    _blacklist: Optional[Set[str]] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._db_keys = {k.lower() for k in self.locations_db.keys()}
        self._load_blacklist()
        # Lazy initialization - strategies loaded on first use

    def _load_blacklist(self) -> None:
        """Load location blacklist for filtering false positives."""
        try:
            from ...location_db import LOCATION_BLACKLIST
            self._blacklist = set(LOCATION_BLACKLIST)
        except Exception:
            self._blacklist = {
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                'saturday', 'sunday', 'january', 'february', 'march',
                'april', 'may', 'june', 'july', 'august', 'september',
                'october', 'november', 'december', 'at', 'to', 'from',
                'in', 'on', 'for', 'with', 'the', 'a', 'an', 'pty', 'ltd',
            }

    def _ensure_initialized(self) -> None:
        """Lazy initialization of strategy instances."""
        if self._initialized:
            return

        errors: List[str] = []

        # Tier 1: Aho-Corasick (fastest exact matching)
        if self.enable_aho_corasick:
            try:
                self._aho_corasick = AhoCorasickStrategy(
                    locations_db=self.locations_db,
                    case_sensitive=False,
                )
            except ImportError as e:
                errors.append(f"Aho-Corasick: {e}")

        # Tier 2: Gazetteer Regex (pattern-based)
        if self.enable_regex:
            try:
                self._regex = GazetteerRegexStrategy(
                    locations_db=self.locations_db,
                )
            except ImportError as e:
                errors.append(f"Regex: {e}")

        # Tier 3: spaCy NER (semantic understanding)
        if self.enable_spacy:
            try:
                self._spacy = SpacyNerStrategy(
                    locations_db=self.locations_db,
                    model=self.spacy_model,
                    models_preference=self.spacy_models_preference,
                )
            except ImportError as e:
                errors.append(f"spaCy: {e}")

        # Tier 4: Phonetic matching (handles typos/misspellings)
        if self.enable_phonetic:
            try:
                self._phonetic = PhoneticGazetteerStrategy(
                    locations_db=self.locations_db,
                    min_token_match_ratio=self.phonetic_min_token_match_ratio,
                )
            except ImportError as e:
                errors.append(f"Phonetic: {e}")

        # Tier 5: TF-IDF (vector space similarity)
        if self.enable_tfidf:
            try:
                self._tfidf = SklearnTfidfStrategy(
                    locations_db=self.locations_db,
                    ngram_range=self.vector_ngram_range,
                    min_df=self.vector_min_df,
                    max_df=self.vector_max_df,
                    max_features=self.vector_max_features,
                    threshold=self.vector_threshold,
                )
            except ImportError as e:
                errors.append(f"TF-IDF: {e}")

        # Alternative: Bag of Words
        if self.enable_bow:
            try:
                self._bow = SklearnBoWStrategy(
                    locations_db=self.locations_db,
                    ngram_range=self.vector_ngram_range,
                    min_df=self.vector_min_df,
                    max_df=self.vector_max_df,
                    max_features=self.vector_max_features,
                    threshold=self.vector_threshold,
                )
            except ImportError as e:
                errors.append(f"BoW: {e}")

        # Country detector for fallback
        try:
            self._country_detector = CountryDetector()
        except ImportError:
            pass

        self._initialized = True

        if errors:
            import logging
            logging.getLogger(__name__).warning(
                f"Some strategies failed to load: {'; '.join(errors)}"
            )

    def _normalize(self, location: str) -> str:
        """Normalize location name for deduplication."""
        return location.lower().strip()

    def _is_valid_match(self, location: str) -> bool:
        """Filter out obvious false positives."""
        loc = self._normalize(location)

        # Too short
        if len(loc) < 2:
            return False

        # In blacklist
        if self._blacklist and loc in self._blacklist:
            return False

        # All digits
        if loc.replace(' ', '').isdigit():
            return False

        return True

    def _calculate_confidence(
            self,
            location: str,
            sources: Set[str],
            in_db: bool,
    ) -> float:
        """
        Calculate confidence score based on extraction sources.

        Confidence factors:
        - In database: +0.3
        - Aho-Corasick (exact): +0.25
        - Regex match: +0.2
        - spaCy NER: +0.2
        - Phonetic: +0.15
        - TF-IDF/BoW: +0.1
        - Multiple sources: +0.1 per additional source
        """
        confidence = 0.0

        if in_db:
            confidence += 0.3

        source_weights = {
            'aho_corasick': 0.25,
            'regex': 0.2,
            'spacy': 0.2,
            'phonetic': 0.15,
            'tfidf': 0.1,
            'bow': 0.1,
            'country': 0.1,
        }

        for source in sources:
            confidence += source_weights.get(source, 0.05)

        # Bonus for multiple sources agreeing
        if len(sources) >= 2:
            confidence += 0.1 * (len(sources) - 1)

        return min(confidence, 1.0)

    def extract(self, text: str) -> List[str]:
        """
        Extract locations from text using ensemble of strategies.

        Args:
            text: Input text to extract locations from

        Returns:
            List of unique location names (lowercase, deduplicated)
        """
        if not text:
            return []

        self._ensure_initialized()

        results: Dict[str, Set[str]] = defaultdict(set)  # location -> sources

        # Tier 1: Aho-Corasick (exact matching - fastest)
        if self._aho_corasick:
            try:
                for loc in self._aho_corasick.extract(text):
                    if self._is_valid_match(loc):
                        results[self._normalize(loc)].add('aho_corasick')
            except Exception:
                pass

        # Tier 2: Regex (pattern-based)
        if self._regex:
            try:
                for loc in self._regex.extract(text):
                    if self._is_valid_match(loc):
                        results[self._normalize(loc)].add('regex')
            except Exception:
                pass

        # If fast methods found results and fallback is disabled, return early
        if results and not self.fallback_on_empty:
            return list(results.keys())

        # Tier 3: spaCy NER (semantic - more expensive)
        if self._spacy:
            try:
                for loc in self._spacy.extract(text):
                    if self._is_valid_match(loc):
                        results[self._normalize(loc)].add('spacy')
            except Exception:
                pass

        # If we have results from fast methods + NER, skip expensive tiers
        # unless we want maximum recall
        if results and len(results) >= 2:
            return list(results.keys())

        # Tier 4: Phonetic matching (handles typos - medium cost)
        if self._phonetic:
            try:
                for loc in self._phonetic.extract(text):
                    if self._is_valid_match(loc):
                        results[self._normalize(loc)].add('phonetic')
            except Exception:
                pass

        # Tier 5: Vector space (most expensive, only if still no results)
        if not results or self.enable_tfidf or self.enable_bow:
            if self._tfidf:
                try:
                    for loc in self._tfidf.extract(text):
                        if self._is_valid_match(loc):
                            results[self._normalize(loc)].add('tfidf')
                except Exception:
                    pass

            if self._bow:
                try:
                    for loc in self._bow.extract(text):
                        if self._is_valid_match(loc):
                            results[self._normalize(loc)].add('bow')
                except Exception:
                    pass

        # Last resort: Country detection
        if not results and self._country_detector:
            try:
                code = self._country_detector.detect_country(text)
                if code:
                    name = self._country_detector.get_country_name(code)
                    if name and self._is_valid_match(name):
                        results[self._normalize(name)].add('country')
            except Exception:
                pass

        return list(results.keys())

    def extract_with_confidence(self, text: str) -> List[Dict]:
        """
        Extract locations with detailed confidence scores and source attribution.

        Args:
            text: Input text to extract locations from

        Returns:
            List of dicts with 'location', 'confidence', 'sources', 'in_database' keys
        """
        if not text:
            return []

        self._ensure_initialized()

        results: Dict[str, Set[str]] = defaultdict(set)

        # Run all enabled strategies
        strategies = [
            (self._aho_corasick, 'aho_corasick'),
            (self._regex, 'regex'),
            (self._spacy, 'spacy'),
            (self._phonetic, 'phonetic'),
            (self._tfidf, 'tfidf'),
            (self._bow, 'bow'),
        ]

        for strategy, name in strategies:
            if strategy:
                try:
                    for loc in strategy.extract(text):
                        if self._is_valid_match(loc):
                            results[self._normalize(loc)].add(name)
                except Exception:
                    pass

        # Country detection fallback
        if not results and self._country_detector:
            try:
                code = self._country_detector.detect_country(text)
                if code:
                    name = self._country_detector.get_country_name(code)
                    if name and self._is_valid_match(name):
                        results[self._normalize(name)].add('country')
            except Exception:
                pass

        # Build detailed results
        db_keys = self._db_keys or set()
        detailed = []
        for location, sources in results.items():
            in_db = location in db_keys
            confidence = self._calculate_confidence(location, sources, in_db)
            detailed.append({
                'location': location,
                'confidence': round(confidence, 3),
                'sources': sorted(sources),
                'in_database': in_db,
            })

        # Sort by confidence (highest first)
        detailed.sort(key=lambda x: -x['confidence'])

        return detailed

    def extract_best(self, text: str, min_confidence: float = 0.3) -> Optional[str]:
        """
        Extract the single best location from text.

        Args:
            text: Input text
            min_confidence: Minimum confidence threshold

        Returns:
            Best location name or None if no confident match
        """
        results = self.extract_with_confidence(text)
        if results and results[0]['confidence'] >= min_confidence:
            return results[0]['location']
        return None

    def get_strategy_status(self) -> Dict[str, bool]:
        """Return status of each strategy (enabled and loaded)."""
        self._ensure_initialized()
        return {
            'aho_corasick': self._aho_corasick is not None,
            'regex': self._regex is not None,
            'spacy': self._spacy is not None,
            'phonetic': self._phonetic is not None,
            'tfidf': self._tfidf is not None,
            'bow': self._bow is not None,
            'country_detector': self._country_detector is not None,
        }
