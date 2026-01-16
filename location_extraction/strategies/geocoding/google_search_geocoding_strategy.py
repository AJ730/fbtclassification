from typing import Any, Dict, List, Optional, Set

from ..base import BaseModel, PrivateAttr

try:  # pydantic v2 config helper
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore


class GoogleSearchGeocodingStrategy(BaseModel):  # type: ignore[misc]
    """
    Refine a query using Google Search page text with lightweight heuristics
    (no spaCy dependency), then geocode with an inner provider. If requests/bs4
    are missing or the refinement fails, it gracefully falls back to the inner
    strategy with the original name.
    """
    inner: Any
    locations_db: Optional[Dict[str, Dict]] = None
    delay_seconds: float = 1.5

    # Allow Protocol/objects as fields (e.g., `inner` strategy instance)
    model_config = ConfigDict(arbitrary_types_allowed=True)  # type: ignore[call-arg]

    _last_ts: float = PrivateAttr(default=0.0)
    _lookup_names: Optional[Set[str]] = PrivateAttr(default_factory=set)
    _state_names: Optional[Set[str]] = PrivateAttr(default_factory=set)
    _state_tokens: Optional[Set[str]] = PrivateAttr(default_factory=set)
    _country_alias_map: Optional[Dict[str, str]] = PrivateAttr(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        # If no explicit locations_db provided, inherit from inner if available
        try:
            if self.locations_db is None and hasattr(self, "inner"):
                inner_db = getattr(self.inner, "locations_db", None)
                if isinstance(inner_db, dict):
                    self.locations_db = inner_db
        except Exception:
            pass
        try:
            names: Set[str] = set()
            states: Set[str] = set()
            state_tokens: Set[str] = set()
            country_alias_map: Dict[str, str] = {}
            try:
                import pycountry  # type: ignore
            except Exception:
                pycountry = None  # type: ignore
            if isinstance(self.locations_db, dict):
                for k, v in self.locations_db.items():
                    if isinstance(k, str) and k:
                        names.add(k.lower())
                    if isinstance(v, dict):
                        st = v.get("state")
                        if isinstance(st, str) and st:
                            st_up = st.upper()
                            states.add(st_up.lower())
                            if len(st_up) == 2 and st_up.isalpha():
                                if pycountry is not None:
                                    c = None
                                    try:
                                        c = pycountry.countries.get(alpha_2=st_up)
                                    except Exception:
                                        c = None
                                    if c and getattr(c, "name", None):
                                        country_alias_map[st_up] = c.name
                                if st_up == "UK":
                                    country_alias_map["UK"] = "United Kingdom"
            try:
                from ...location_db import STATE_MAPPING  # type: ignore
                for tok in STATE_MAPPING.keys():
                    if isinstance(tok, str) and tok:
                        state_tokens.add(tok.lower())
                for abbr in STATE_MAPPING.values():
                    if isinstance(abbr, str) and abbr:
                        state_tokens.add(abbr.lower())
            except Exception:
                pass
            self._lookup_names = names
            self._state_names = states
            self._state_tokens = state_tokens
            self._country_alias_map = country_alias_map
        except Exception:
            self._lookup_names = set()
            self._state_names = set()
            self._state_tokens = set()
            self._country_alias_map = {}

    def _rate_limit(self):
        import time
        elapsed = time.time() - (self._last_ts or 0.0)
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_ts = time.time()

    def _extract_context_terms(self, text: str, target: str) -> Optional[str]:
        import re as _re
        text = text[:8000]
        lower = text.lower()
        target_lower = target.lower()
        positions = [_m.start() for _m in _re.finditer(_re.escape(target_lower), lower)]
        if not positions:
            return None
        candidates: List[str] = []
        for p in positions:
            start = max(0, p - 200)
            end = min(len(text), p + 200)
            window = text[start:end]
            tokens = _re.findall(r"\b[A-Z][A-Za-z'\-]{2,}\b", window)
            candidates.extend(tokens)
        names = self._lookup_names or set()
        states = self._state_names or set()
        state_tokens = self._state_tokens or set()
        country_alias_map = self._country_alias_map or {}
        for cand in candidates:
            lc = cand.lower()
            if lc in state_tokens or lc in states:
                return cand
            if lc in names:
                return cand
            uc = cand.upper()
            if uc in country_alias_map:
                return country_alias_map[uc]
        if candidates:
            from collections import Counter
            return Counter(candidates).most_common(1)[0][0]
        return None

    def _refine_query(self, entity: str, context: Optional[str]) -> Optional[str]:
        query = f"where is {entity} located city country"
        try:
            import requests  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore
            from urllib.parse import quote_plus
        except Exception:
            return None
        try:
            self._rate_limit()
            url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if getattr(resp, "status_code", 500) != 200:
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            page_text = soup.get_text(separator=" ", strip=True)
            ctx = self._extract_context_terms(page_text, entity)
            if ctx:
                return f"{entity}, {ctx}"
            return None
        except Exception:
            return None

    def geocode(self, location_name: str, context: Optional[str] = None) -> Optional[Dict]:
        if not location_name:
            return None
        refined = self._refine_query(location_name, context)
        return self.inner.geocode(refined or location_name, context)
