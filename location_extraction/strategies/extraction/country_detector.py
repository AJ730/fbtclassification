"""
Country and Australian state detector for location extraction fallback.
Lightweight implementation without pycountry dependency.
"""
import re
from typing import Dict, List, Optional, Tuple

from ..base import BaseModel, PrivateAttr

# Common country names/aliases -> ISO alpha-2 codes (lowercase)
COUNTRY_ALIASES: Dict[str, str] = {
    # Full names
    'australia': 'au', 'united states': 'us', 'united kingdom': 'gb',
    'new zealand': 'nz', 'singapore': 'sg', 'hong kong': 'hk',
    'united arab emirates': 'ae', 'japan': 'jp', 'china': 'cn',
    'indonesia': 'id', 'thailand': 'th', 'malaysia': 'my',
    'philippines': 'ph', 'india': 'in', 'germany': 'de',
    'france': 'fr', 'italy': 'it', 'spain': 'es', 'netherlands': 'nl',
    'canada': 'ca', 'mexico': 'mx', 'brazil': 'br', 'south korea': 'kr',
    'taiwan': 'tw', 'vietnam': 'vn', 'south africa': 'za',
    # Abbreviations
    'usa': 'us', 'uk': 'gb', 'uae': 'ae',
    # Colloquial
    'america': 'us', 'britain': 'gb', 'england': 'gb', 'holland': 'nl',
    'great britain': 'gb',
}

# ISO alpha-2 code -> display name
CODE_TO_NAME: Dict[str, str] = {
    'au': 'Australia', 'us': 'United States', 'gb': 'United Kingdom',
    'nz': 'New Zealand', 'sg': 'Singapore', 'hk': 'Hong Kong',
    'ae': 'United Arab Emirates', 'jp': 'Japan', 'cn': 'China',
    'id': 'Indonesia', 'th': 'Thailand', 'my': 'Malaysia',
    'ph': 'Philippines', 'in': 'India', 'de': 'Germany',
    'fr': 'France', 'it': 'Italy', 'es': 'Spain', 'nl': 'Netherlands',
    'ca': 'Canada', 'mx': 'Mexico', 'br': 'Brazil', 'kr': 'South Korea',
    'tw': 'Taiwan', 'vn': 'Vietnam', 'za': 'South Africa',
}

# Australian states
AU_STATE_MAPPING: Dict[str, str] = {
    'nsw': 'NSW', 'new south wales': 'NSW',
    'vic': 'VIC', 'victoria': 'VIC',
    'qld': 'QLD', 'queensland': 'QLD',
    'wa': 'WA', 'western australia': 'WA',
    'sa': 'SA', 'south australia': 'SA',
    'tas': 'TAS', 'tasmania': 'TAS',
    'nt': 'NT', 'northern territory': 'NT',
    'act': 'ACT', 'australian capital territory': 'ACT',
}


class CountryDetector(BaseModel):  # type: ignore[misc]
    """
    Detect country or Australian state from free text.
    Used as a fallback when NER-based extraction finds nothing.
    """

    _name_to_code: Optional[Dict[str, str]] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._name_to_code = {k.lower(): v.lower() for k, v in COUNTRY_ALIASES.items()}

    def detect_country(self, text: str) -> Optional[str]:
        """
        Detect country code from text.
        Returns ISO alpha-2 code (lowercase) or None.
        """
        if not text:
            return None

        hay = text.lower()
        matches: List[Tuple[str, str, int]] = []

        for name, code in (self._name_to_code or {}).items():
            if len(name) < 2:
                continue
            # Word boundary match
            if re.search(r'\b' + re.escape(name) + r'\b', hay):
                matches.append((name, code, len(name)))

        if not matches:
            return None

        # Return longest match (most specific)
        matches.sort(key=lambda x: -x[2])
        return matches[0][1]

    def get_country_name(self, code: str) -> Optional[str]:
        """
        Get country display name from ISO alpha-2 code.
        Returns country name or None if unknown.
        """
        if not code:
            return None
        return CODE_TO_NAME.get(code.lower())

    def detect_au_state(self, text: str) -> Optional[str]:
        """
        Detect Australian state from text.
        Returns state abbreviation (e.g., 'NSW') or None.
        """
        if not text:
            return None

        hay = text.lower()

        for pattern, abbr in AU_STATE_MAPPING.items():
            if re.search(r'\b' + re.escape(pattern) + r'\b', hay):
                return abbr

        return None