from typing import Any, Dict, List, Optional

from ..base import BaseModel, GeocodingStrategy

try:  # pydantic v2 config helper
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore


class ChainedGeocodingStrategy(BaseModel):  # type: ignore[misc]
    """Try a list of geocoders in order; return the first successful result."""
    strategies: List[Any]

    # Allow Protocol/objects as fields (list of strategy instances)
    model_config = ConfigDict(arbitrary_types_allowed=True)  # type: ignore[call-arg]

    def __init__(self, **data):
        super().__init__(**data)
        try:
            items = list(self.strategies or [])
            # Drop Nones and keep order
            self.strategies = [s for s in items if s is not None]
        except Exception:
            self.strategies = []

    def geocode(self, location_name: str, context: Optional[str] = None) -> Optional[Dict]:
        for s in self.strategies:
            try:
                r = s.geocode(location_name, context)
            except Exception:
                r = None
            if r:
                return r
        return None
