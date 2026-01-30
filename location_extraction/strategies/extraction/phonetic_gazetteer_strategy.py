import re
from typing import Dict, List, Optional, Set

from ..base import BaseModel, PrivateAttr


class PhoneticGazetteerStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    min_token_match_ratio: float = 0.5

    _name_tokens: Optional[Dict[str, List[str]]] = PrivateAttr(default_factory=dict)
    _token_meta_index: Optional[Dict[str, Set[str]]] = PrivateAttr(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        try:
            import jellyfish  # type: ignore  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise ImportError("jellyfish is required for PhoneticGazetteerStrategy") from e
        self._build_indexes()

    def _metaphone(self, word: str) -> str:
        import jellyfish  # type: ignore
        return jellyfish.metaphone(word) or ""

    def _tokenize(self, s: str) -> List[str]:
        return re.findall(r"[\w'-]+", s.lower())

    def _build_indexes(self):
        name_tokens: Dict[str, List[str]] = {}
        token_meta_index: Dict[str, Set[str]] = {}
        for name in self.locations_db.keys():
            toks = self._tokenize(name)
            metas = [self._metaphone(t) for t in toks if t]
            name_tokens[name] = metas
            for m in metas:
                if not m:
                    continue
                token_meta_index.setdefault(m, set()).add(name)
        self._name_tokens = name_tokens
        self._token_meta_index = token_meta_index

    def extract(self, text: str) -> List[str]:
        if not text:
            return []
        toks = self._tokenize(text)
        metas = [self._metaphone(t) for t in toks if t]
        cand_counts: Dict[str, int] = {}
        inv = self._token_meta_index or {}
        for m in metas:
            if not m:
                continue
            for name in inv.get(m, set()):
                cand_counts[name] = cand_counts.get(name, 0) + 1
        res: Set[str] = set()
        name_meta = self._name_tokens or {}
        for name, cnt in cand_counts.items():
            total = max(1, len([x for x in name_meta.get(name, []) if x]))
            ratio = cnt / total
            if ratio >= self.min_token_match_ratio:
                res.add(name.lower())
        return list(res)