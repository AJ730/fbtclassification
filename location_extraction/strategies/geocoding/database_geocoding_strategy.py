from typing import Dict, Optional

from ..base import BaseModel


class DatabaseGeocodingStrategy(BaseModel):  # type: ignore[misc]
    """Lookup coordinates from the in-memory gazetteer (locations_db)."""
    locations_db: Dict[str, Dict]

    def __init__(self, **data):
        super().__init__(**data)
        try:
            src = self.locations_db if isinstance(self.locations_db, dict) else {}
            normalized: Dict[str, Dict] = {}
            for k, v in src.items():
                if not isinstance(k, str) or not isinstance(v, dict):
                    continue
                key = k.lower().strip()
                lat = v.get("lat")
                lon = v.get("lon")
                if lat is None or lon is None:
                    continue
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                except Exception:
                    continue
                normalized[key] = {**v, "lat": lat_f, "lon": lon_f}
            self.locations_db = normalized
        except Exception:
            self.locations_db = {}

    def geocode(self, location_name: str, context: Optional[str] = None) -> Optional[Dict]:
        if not location_name:
            return None
        key = location_name.lower().strip()
        return self.locations_db.get(key)
