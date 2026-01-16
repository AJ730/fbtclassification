import re
from typing import Dict, List, Optional, Set

from ..base import BaseModel, PrivateAttr


class NltkNerStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    download_if_missing: bool = True

    _ready: Optional[bool] = PrivateAttr(default=False)
    _keys: Optional[Set[str]] = PrivateAttr(default_factory=set)

    def __init__(self, **data):
        super().__init__(**data)
        self._keys = {k.lower() for k in self.locations_db.keys()}
        try:
            import nltk  # type: ignore
            self._ensure_nltk(nltk)
            self._ready = True
        except Exception as e:  # pragma: no cover
            raise ImportError("nltk with required models is needed for NltkNerStrategy") from e

    def _ensure_nltk(self, nltk):
        req = [
            "punkt",
            "averaged_perceptron_tagger",
            "maxent_ne_chunker",
            "words",
        ]
        for r in req:
            try:
                nltk.data.find(r)
            except LookupError:
                if self.download_if_missing:
                    nltk.download(r, quiet=True)
                else:
                    raise

    def extract(self, text: str) -> List[str]:
        if not text or not self._ready:
            return []
        from nltk import word_tokenize, pos_tag, ne_chunk  # type: ignore
        ents: Set[str] = set()
        try:
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            tree = ne_chunk(tagged)
            for subtree in tree:
                if hasattr(subtree, 'label') and subtree.label() in ("GPE", "LOCATION"):
                    name = " ".join([leaf[0] for leaf in subtree.leaves()])
                    ents.add(name.lower())
        except Exception:
            pass
        keys = self._keys or set()
        matches = {e for e in ents if e in keys}
        if not matches:
            tokens = {t.lower() for t in re.findall(r"[\w'-]+", text)}
            matches = tokens.intersection(keys)
        return list(matches)
