from typing import Dict, Literal, Optional, Tuple, Union

from .vector_space_base import VectorSpaceGazetteerStrategy


class SklearnBoWStrategy(VectorSpaceGazetteerStrategy):  # type: ignore[misc]
    """Bag-of-Words strategy using CountVectorizer."""

    # Redeclare for type-checker (inherited from parent)
    locations_db: Dict[str, Dict]
    vectorizer_type: Literal["count", "tfidf"] = "count"
    ngram_range: Tuple[int, int] = (1, 3)
    min_df: int = 1
    max_df: Union[int, float] = 0.9
    max_features: Optional[int] = None
    threshold: float = 0.2