from typing import Dict, List, Optional

from ..base import BaseModel, PrivateAttr


class RapidFuzzFuzzyStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    threshold: int = 85  # 0-100
    limit: int = 15
    scorer: str = "token_set_ratio"  # ratio, partial_ratio, token_sort_ratio, token_set_ratio

    _names: Optional[List[str]] = PrivateAttr(default_factory=list)

    def __init__(self, **data):
        super().__init__(**data)
        try:
            import rapidfuzz  # type: ignore  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise ImportError("rapidfuzz is required for RapidFuzzFuzzyStrategy") from e
        self._names = list(self.locations_db.keys())

    def _get_scorer(self):
        from rapidfuzz import fuzz  # type: ignore
        return {
            "ratio": fuzz.ratio,
            "partial_ratio": fuzz.partial_ratio,
            "token_sort_ratio": fuzz.token_sort_ratio,
            "token_set_ratio": fuzz.token_set_ratio,
        }.get(self.scorer, fuzz.token_set_ratio)

    def extract(self, text: str) -> List[str]:
        if not text:
            return []
        from rapidfuzz import process  # type: ignore
        names = self._names or []
        scorer = self._get_scorer()
        hits = process.extract(text, names, scorer=scorer, limit=self.limit)
        res = {name.lower() for name, score, _ in hits if score >= self.threshold}
        return list(res)
