from typing import Dict, List, Literal, Optional, Tuple

from location_extraction.strategies.base import BaseModel, PrivateAttr


class VectorSpaceGazetteerStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, Dict]
    vectorizer_type: Literal["count", "tfidf"] = "tfidf"
    ngram_range: Tuple[int, int] = (1, 3)
    min_df: int = 1
    max_features: Optional[int] = None
    threshold: float = 0.2

    _vectorizer: Optional[object] = PrivateAttr(default=None)
    _matrix: Optional[object] = PrivateAttr(default=None)
    _names: Optional[List[str]] = PrivateAttr(default_factory=list)

    def __init__(self, **data):
        super().__init__(**data)
        try:
            from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer  # type: ignore
            from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise ImportError("scikit-learn is required for VectorSpace strategies") from e

        docs = sorted(self.locations_db.keys(), key=len, reverse=True)
        self._names = docs
        if self.vectorizer_type == "count":
            vec = CountVectorizer(ngram_range=self.ngram_range, min_df=self.min_df, max_features=self.max_features)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            vec = TfidfVectorizer(ngram_range=self.ngram_range, min_df=self.min_df, max_features=self.max_features)
        self._vectorizer = vec
        self._matrix = vec.fit_transform(docs)

    def extract(self, text: str) -> List[str]:
        if not text:
            return []
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
        Xq = self._vectorizer.transform([text])  # type: ignore[union-attr]
        sims = cosine_similarity(self._matrix, Xq).ravel()  # type: ignore[union-attr]
        names = self._names or []
        hits = [names[i] for i, s in enumerate(sims) if s >= self.threshold]
        return list({h.lower() for h in hits})
