from typing import Dict, List, Optional, Tuple

from ..base import BaseModel, PrivateAttr


class CountryDetector(BaseModel):  # type: ignore[misc]
    """Detect country from free text using pycountry and centralized aliases.

    Also exposes a lightweight AU state detector using STATE_MAPPING
    in location_db (if available).
    """

    _name_to_code: Optional[Dict[str, str]] = PrivateAttr(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        self._build_lookups()

    def _build_lookups(self):
        table: Dict[str, str] = {}
        try:
            import pycountry  # type: ignore
            for country in pycountry.countries:
                code = str(getattr(country, "alpha_2", "")).lower()
                name = str(getattr(country, "name", "")).lower()
                if code and name:
                    table[name] = code
                common = getattr(country, "common_name", None)
                if common:
                    table[str(common).lower()] = code
                alpha3 = str(getattr(country, "alpha_3", "")).lower()
                if len(alpha3) >= 3:
                    table[alpha3] = code
        except Exception:
            pass

        try:
            from ...location_db import COUNTRY_ALIASES  # type: ignore
            table.update({k.lower(): v for k, v in COUNTRY_ALIASES.items()})
        except Exception:
            pass

        self._name_to_code = table

    def detect_country(self, text: str) -> Optional[str]:
        if not text:
            return None
        hay = text.lower()
        import re as _re
        matches: List[Tuple[str, str, int]] = []
        for name, code in (self._name_to_code or {}).items():
            if len(name) < 3:
                continue
            pat = r"\b" + _re.escape(name) + r"\b"
            if _re.search(pat, hay):
                matches.append((name, code, len(name)))
        if not matches:
            return None
        matches.sort(key=lambda x: -x[2])
        return matches[0][1]

    def get_country_name(self, code: str) -> Optional[str]:
        try:
            import pycountry  # type: ignore
            c = pycountry.countries.get(alpha_2=str(code).upper())
            return c.name if c else None
        except Exception:
            return None

    def detect_au_state(self, text: str) -> Optional[str]:
        try:
            from ...location_db import STATE_MAPPING  # type: ignore
        except Exception:
            return None
        if not text:
            return None
        hay = text.lower()
        import re as _re
        for tok, abbr in STATE_MAPPING.items():
            if not tok:
                continue
            pat = r"\b" + _re.escape(tok.lower()) + r"\b"
            if _re.search(pat, hay):
                return STATE_MAPPING.get(tok)
        for abbr in STATE_MAPPING.values():
            if not abbr:
                continue
            pat = r"\b" + _re.escape(str(abbr).lower()) + r"\b"
            if _re.search(pat, hay):
                return str(abbr)
        return None
