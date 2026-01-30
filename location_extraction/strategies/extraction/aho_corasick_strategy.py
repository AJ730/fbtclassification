from typing import Dict, List, Optional

from ..base import BaseModel, PrivateAttr


class AhoCorasickStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    case_sensitive: bool = False

    _automaton: Optional[object] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        try:
            import ahocorasick  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError("pyahocorasick is required for AhoCorasickStrategy") from e

        A = ahocorasick.Automaton()
        for name in self.locations_db.keys():
            key = name if self.case_sensitive else name.lower()
            if key not in A:
                A.add_word(key, key)
        A.make_automaton()
        self._automaton = A

    def extract(self, text: str) -> List[str]:
        if not text or self._automaton is None:
            return []
        hay = text if self.case_sensitive else text.lower()
        A = self._automaton  # type: ignore[assignment]
        res = {match for _, match in A.iter(hay)}  # type: ignore[attr-defined]
        return list({r.lower() for r in res})