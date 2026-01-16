import re
from typing import Dict, Dict as _Dict, Pattern, Optional, List

from ..base import BaseModel, PrivateAttr


class GazetteerRegexStrategy(BaseModel):  # type: ignore[misc]
    locations_db: Dict[str, _Dict]
    _pattern: Optional[Pattern[str]] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        location_names = sorted(self.locations_db.keys(), key=len, reverse=True)
        escaped_names = [re.escape(name) for name in location_names]
        self._pattern = (
            re.compile(r"\b(" + "|".join(escaped_names) + r")\b", re.IGNORECASE)
            if escaped_names
            else None
        )

    def extract(self, text: str) -> List[str]:
        if not text or self._pattern is None:
            return []
        matches = self._pattern.findall(str(text))
        return list({m.lower() for m in matches})
