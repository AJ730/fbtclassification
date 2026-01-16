from typing import Literal
from .vector_space_base import VectorSpaceGazetteerStrategy


class SklearnTfidfStrategy(VectorSpaceGazetteerStrategy):  # type: ignore[misc]
    vectorizer_type: Literal["count", "tfidf"] = "tfidf"
