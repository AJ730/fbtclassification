"""
NLTK-based Named Entity Recognition strategy for location extraction.
Uses NLTK's ne_chunk for basic NER without requiring spaCy.
"""
import re
from typing import Dict, List, Optional, Set

from ..base import BaseModel, PrivateAttr


class NltkNerStrategy(BaseModel):  # type: ignore[misc]
    """
    Extract locations using NLTK's named entity recognition.

    This is a lighter-weight alternative to spaCy that doesn't require
    downloading large models. Uses NLTK's ne_chunk with Penn Treebank
    POS tagging.
    """
    locations_db: Dict[str, Dict]

    _nltk_available: bool = PrivateAttr(default=False)
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
        self._check_nltk()

    def _check_nltk(self) -> None:
        """Check if NLTK and required data are available."""
        try:
            import nltk
            # Check for required NLTK data
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('taggers/averaged_perceptron_tagger')
                nltk.data.find('chunkers/maxent_ne_chunker')
                nltk.data.find('corpora/words')
                self._nltk_available = True
            except LookupError:
                # Try to download required data
                try:
                    nltk.download('punkt', quiet=True)
                    nltk.download('averaged_perceptron_tagger', quiet=True)
                    nltk.download('maxent_ne_chunker', quiet=True)
                    nltk.download('words', quiet=True)
                    nltk.download('punkt_tab', quiet=True)
                    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
                    nltk.download('maxent_ne_chunker_tab', quiet=True)
                    self._nltk_available = True
                except Exception:
                    self._nltk_available = False
        except ImportError:
            self._nltk_available = False

    def _extract_entities(self, text: str) -> List[str]:
        """Extract GPE (Geo-Political Entity) and LOCATION entities using NLTK."""
        if not self._nltk_available:
            return []

        try:
            import nltk
            from nltk import word_tokenize, pos_tag, ne_chunk
            from nltk.tree import Tree
        except ImportError:
            return []

        entities = []

        try:
            # Tokenize and POS tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)

            # Named entity chunking
            tree = ne_chunk(pos_tags)

            # Extract GPE and LOCATION entities
            for subtree in tree:
                if isinstance(subtree, Tree):
                    entity_type = subtree.label()
                    if entity_type in ('GPE', 'LOCATION', 'FACILITY'):
                        entity_name = ' '.join([token for token, pos in subtree.leaves()])
                        entities.append(entity_name)
        except Exception:
            pass

        return entities

    def extract(self, text: str) -> List[str]:
        """
        Extract locations from text using NLTK NER.

        Args:
            text: Input text to extract locations from

        Returns:
            List of location names found (lowercase, filtered against DB)
        """
        if not text or not self._nltk_available:
            return []

        # Get NER entities
        entities = self._extract_entities(text)

        # Filter against blacklist
        bl = self._blacklist or set()
        candidates = []
        for ent in entities:
            ent_lower = ent.lower().strip()
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