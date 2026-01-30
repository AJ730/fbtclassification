import math


class FeatureCalculator:
    """Compute distance-based features and simple travel estimates."""

    def __init__(self, reference_coords):
        self.ref_lat, self.ref_lon = reference_coords

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlmb = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def distance_km(self, lat: float, lon: float) -> float:
        return self._haversine(self.ref_lat, self.ref_lon, lat, lon)

    def est_travel_hours(self, distance_km: float) -> float:
        if distance_km <= 0:
            return 0.0
        if distance_km < 300:
            return distance_km / 70.0
        return 2.5 + (distance_km / 800.0)
