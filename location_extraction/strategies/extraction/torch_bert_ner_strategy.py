"""
PyTorch BERT-based Named Entity Recognition strategy for location extraction.
Uses HuggingFace transformers for state-of-the-art NER.

Note: This is an optional strategy that requires torch and transformers.
It provides the highest accuracy but is also the most resource-intensive.
"""
import re
from typing import Dict, List, Optional, Set, Any

from ..base import BaseModel, PrivateAttr


class TorchBertNerStrategy(BaseModel):  # type: ignore[misc]
    """
    Extract locations using BERT-based NER from HuggingFace transformers.

    This provides state-of-the-art NER accuracy but requires:
    - torch
    - transformers
    - A pre-trained NER model (default: dslim/bert-base-NER)

    Due to the heavy dependencies, this strategy gracefully degrades
    to a no-op if the required packages are not installed.
    """
    locations_db: Dict[str, Dict]
    model_name: str = "dslim/bert-base-NER"
    device: str = "cpu"  # or "cuda" for GPU

    _pipeline: Optional[Any] = PrivateAttr(default=None)
    _available: bool = PrivateAttr(default=False)
    _keys: Optional[Set[str]] = PrivateAttr(default=None)
    _blacklist: Optional[Set[str]] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._keys = {k.lower() for k in self.locations_db.keys()}
        self._blacklist = {
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'saturday', 'sunday', 'january', 'february', 'march',
            'april', 'may', 'june', 'july', 'august', 'september',
            'october', 'november', 'december', 'at', 'to', 'from',
            'in', 'on', 'for', 'with', 'the', 'a', 'an', 'pty', 'ltd',
        }
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load the BERT NER pipeline."""
        try:
            from transformers import pipeline
            self._pipeline = pipeline(
                "ner",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
                aggregation_strategy="simple",
            )
            self._available = True
        except ImportError:
            # transformers or torch not installed
            self._available = False
        except Exception:
            # Model loading failed
            self._available = False

    def _extract_entities(self, text: str) -> List[str]:
        """Extract location entities using BERT NER."""
        if not self._available or self._pipeline is None:
            return []

        entities = []

        try:
            # Run NER pipeline
            results = self._pipeline(text)

            # Filter for location-related entities
            # BERT-NER typically uses: B-LOC, I-LOC for locations
            for entity in results:
                entity_group = entity.get("entity_group", entity.get("entity", ""))
                if entity_group in ("LOC", "GPE", "LOCATION", "B-LOC", "I-LOC"):
                    word = entity.get("word", "").strip()
                    if word and not word.startswith("##"):
                        entities.append(word)
        except Exception:
            pass

        return entities

    def extract(self, text: str) -> List[str]:
        """
        Extract locations from text using BERT NER.

        Args:
            text: Input text to extract locations from

        Returns:
            List of location names found (lowercase, filtered against DB)
        """
        if not text or not self._available:
            return []

        # Get NER entities
        entities = self._extract_entities(text)

        # Filter against blacklist
        bl = self._blacklist or set()
        candidates = []
        for ent in entities:
            ent_lower = ent.lower().strip()
            # Remove BERT subword markers
            ent_lower = ent_lower.replace("##", "")
            if ent_lower not in bl and len(ent_lower) >= 3:
                candidates.append(ent_lower)

        # If no NER results, try simple token matching
        if not candidates:
            tokens = set(re.findall(r"[\w'-]+", text.lower()))
            candidates = list(tokens)

        # Filter against locations database
        keys = self._keys or set()
        matches = [c for c in candidates if c in keys]

        return list(set(matches))

    def is_available(self) -> bool:
        """Check if the BERT NER strategy is available."""
        return self._available