from typing import Dict, Optional

from ..base import BaseModel, PrivateAttr


class NominatimGeocodingStrategy(BaseModel):  # type: ignore[misc]
    """Geocode via geopy Nominatim (online)."""
    country_hint: Optional[str] = "Australia"

    _ready: Optional[bool] = PrivateAttr(default=False)
    _geo: Optional[object] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        try:
            from geopy.geocoders import Nominatim  # type: ignore
            self._geo = Nominatim(user_agent="fbt_classifier")
            self._ready = True
        except Exception:
            self._ready = False

    def geocode(self, location_name: str, context: Optional[str] = None) -> Optional[Dict]:
        if not self._ready or not location_name:
            return None
        query = location_name
        try:
            if self.country_hint and self.country_hint.lower() not in (query.lower()):
                query = f"{location_name}, {self.country_hint}"
            r = self._geo.geocode(query, language="en")  # type: ignore[union-attr]
            if not r and self.country_hint:
                r = self._geo.geocode(f"{location_name}, {self.country_hint}", language="en")  # type: ignore[union-attr]
            if not r:
                return None
            raw = getattr(r, "raw", {}) or {}
            addr = raw.get("address", {}) if isinstance(raw, dict) else {}
            return {
                "lat": getattr(r, "latitude", None),
                "lon": getattr(r, "longitude", None),
                "country": addr.get("country", ""),
                "country_code": (addr.get("country_code", "") or "").upper(),
                "state": addr.get("state", addr.get("region", "")),
                "city": addr.get("city", addr.get("town", addr.get("village", addr.get("suburb", "")))),
                "type": raw.get("type", ""),
                "display_name": raw.get("display_name", ""),
            }
        except Exception:
            return None
