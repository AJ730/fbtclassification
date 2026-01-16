import re
import importlib.util
from typing import Dict, List, Optional, Set, Any

import spacy
from spacy.util import is_package

from ..base import BaseModel, PrivateAttr
from .country_detector import CountryDetector


class SpacyNerStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    model: str = "en_core_web_sm"
    models_preference: Optional[List[str]] = None

    _nlp: Optional[Any] = PrivateAttr(default=None)
    _keys: Optional[Set[str]] = PrivateAttr(default_factory=set)
    _country: Optional[CountryDetector] = PrivateAttr(default=None)
    _blacklist: Optional[Set[str]] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._keys = {k.lower() for k in self.locations_db.keys()}
        self._nlp = self._load_spacy_pipeline()
        self._country = CountryDetector()
        try:
            from ...location_db import LOCATION_BLACKLIST  # type: ignore
            self._blacklist = set(LOCATION_BLACKLIST)
        except Exception:
            self._blacklist = set()

    def _load_spacy_pipeline(self):
        prefs = list(self.models_preference or [])
        if self.model and self.model not in prefs:
            prefs.insert(0, self.model)
        if not prefs:
            prefs = [
                "en_core_web_trf",
                "en_core_web_lg",
                "en_core_web_md",
                "en_core_web_sm",
                "xx_ent_wiki_sm",
            ]
        for m in prefs:
            available = False
            if is_package(m):
                available = True
            elif importlib.util.find_spec(m) is not None:
                available = True
            if available:
                return spacy.load(m)
        raise ImportError(
            "Failed to load any spaCy model. Tried: " + ", ".join(prefs) +
            "\nInstall one, e.g.: python -m spacy download en_core_web_sm"
        )

    def _normalize_text(self, text: str) -> str:
        if not text:
            return text
        parts = text.split()
        out: List[str] = []
        bl = self._blacklist or set()
        for w in parts:
            base = re.sub(r"^[^A-Za-z0-9]*|[^A-Za-z0-9]*$", "", w)
            if base.islower() and len(base) >= 3 and base not in bl:
                out.append(w.replace(base, base.title()))
            else:
                out.append(w)
        return " ".join(out)

    def _extract_from_doc(self, doc) -> List[str]:
        cand: List[str] = []
        nlp = self._nlp  # type: ignore[assignment]
        bl = self._blacklist or set()
        for ent in doc.ents:
            word = ent.text.strip()
            if ent.label_ in ("GPE", "LOC"):
                if word.lower() in bl or len(word) < 3:
                    continue
                cand.append(word)
            elif ent.label_ in ("ORG", "FAC") and nlp is not None:
                try:
                    sub = nlp(word)
                    for e2 in sub.ents:
                        if e2.label_ == "GPE":
                            cand.append(e2.text.strip())
                            break
                except Exception:
                    pass
        return cand

    def extract(self, text: str) -> List[str]:
        if not text or self._nlp is None:
            return []
        nlp = self._nlp  # type: ignore[assignment]
        doc = nlp(text)  # type: ignore[operator]
        cand = self._extract_from_doc(doc)

        if len(cand) < 2:
            norm = self._normalize_text(text)
            if norm != text:
                try:
                    cand2 = self._extract_from_doc(nlp(norm))  # type: ignore[operator]
                    seen: Set[str] = set()
                    merged: List[str] = []
                    for w in cand + cand2:
                        lw = w.lower()
                        if lw not in seen:
                            seen.add(lw)
                            merged.append(w)
                    cand = merged
                except Exception:
                    pass

        if self._country is not None and not cand:
            try:
                code = self._country.detect_country(text)
                if code:
                    cname = self._country.get_country_name(code)
                    if cname:
                        cand.append(cname)
            except Exception:
                pass

        keys = self._keys or set()
        names = {w.lower() for w in cand}
        if not names:
            tokens = {t.lower() for t in re.findall(r"[\w'-]+", text)}
            names = tokens
        matches = names.intersection(keys)
        return list(matches)
