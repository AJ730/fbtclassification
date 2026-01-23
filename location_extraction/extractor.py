from typing import Dict, List, Optional
import math
import numpy as np
import pandas as pd

from .location_db import AUSTRALIAN_LOCATIONS
from .feature_calculator import FeatureCalculator
from .location_validator import LocationValidator
from .strategies import LocationExtractionStrategy, GeocodingStrategy
from .strategies.geocoding import NominatimGeocodingStrategy, GoogleSearchGeocodingStrategy


CONFIG = {
    'reference_location': {'lat': -33.8688, 'lon': 151.2093, 'name': 'Sydney CBD'},
    'enable_geocoding': True,
}


class LocationExtractor:
    """Extract and geocode locations from expense descriptions."""

    def __init__(
        self,
        reference_location: Optional[Dict] = None,
        strategy: Optional[LocationExtractionStrategy] = None,
        geocoding_strategy: Optional[GeocodingStrategy] = None,
    ):
        self.locations_db = AUSTRALIAN_LOCATIONS
        self.reference = reference_location or CONFIG['reference_location']
        self.cache = {}
        self.validator = LocationValidator(self.locations_db)

        self.strategy = strategy
        self._geocoder = geocoding_strategy or GoogleSearchGeocodingStrategy(inner=NominatimGeocodingStrategy(country_hint="Australia"))
        self._feature_calc = FeatureCalculator((self.reference['lat'], self.reference['lon']))

    def extract_locations(self, text: str) -> List[str]:
        if pd.isna(text) or not text:
            return []
        if self.strategy is None:
            return []
        return self.strategy.extract(str(text))

    def _extract_unfiltered_locations(self, text: str) -> List[str]:
        """
        Extract locations without filtering against DB.
        Used as fallback when DB-filtered extraction returns no results.
        Attempts to extract any GPE/LOC entities from spaCy NER.
        """
        if pd.isna(text) or not text or self.strategy is None:
            return []
        
        try:
            # Try to extract without DB filtering by using spaCy directly
            from .strategies.extraction.spacy_ner_strategy import SpacyNerStrategy
            if isinstance(self.strategy, SpacyNerStrategy):
                # Use spaCy's raw NER output without DB filtering
                nlp = self.strategy._nlp
                if nlp:
                    doc = nlp(str(text))
                    locations = []
                    for ent in doc.ents:
                        if ent.label_ in ("GPE", "LOC"):
                            loc = ent.text.strip().lower()
                            if len(loc) >= 3 and loc not in locations:
                                locations.append(loc)
                    return locations
        except Exception:
            pass
        
        return []

    def get_coordinates(self, location_name: str, context: Optional[str] = None) -> Optional[Dict]:
        location_name = location_name.lower().strip()
        if location_name in self.cache:
            return self.cache[location_name]
        
        # Try DB first
        loc = self.locations_db.get(location_name)
        if loc:
            coords = {'lat': loc['lat'], 'lon': loc['lon'], 'type': loc.get('type', 'city'), 'state': loc.get('state', '')}
            self.cache[location_name] = coords
            return coords
        
        # Then API
        if self._geocoder:
            coords = self._geocoder.geocode(location_name, context)
            if coords:
                self.cache[location_name] = coords
                return coords
        return None

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = (math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def estimate_travel_time(self, distance_km: float, travel_type: str = 'auto') -> float:
        if distance_km <= 0:
            return 0
        if travel_type == 'flight' or distance_km > 500:
            return (distance_km / 800) + 2
        elif travel_type == 'car' or distance_km <= 500:
            return distance_km / 80
        else:
            return distance_km / 80

    def extract_location_features(self, text: str, allow_online_fallback: bool = False) -> Dict:
        """
        Extract locations with hybrid approach:
        1. Extract DB-filtered locations from strategy
        2. Geocode using DB-first lookup (fast and reliable)
        3. If allow_online_fallback=True and no geocoded results found,
           try online extraction/geocoding for unmatched locations
        """
        features = {
            'locations_found': 0,
            'location_names': '',
            'primary_location': '',
            'primary_state': '',
            'primary_lat': np.nan,
            'primary_lon': np.nan,
            'distance_from_ref_km': np.nan,
            'estimated_travel_hours': np.nan,
            'is_international': 0,
            'is_regional': 0,
            'is_major_city': 0,
            'is_local': 0,
            'is_interstate': 0,
            'is_remote': 0,
            'travel_category': 'unknown',
            'extracted_locations': '',
            'extracted_count': 0,
            'validation_confidence': 0.0,
            'validation_reasons': '',
            'is_valid_location': 0,
        }

        locations = self.extract_locations(text)
        if not locations:
            return features

        features['extracted_locations'] = ', '.join(locations)
        features['extracted_count'] = len(locations)

        # Filter locations to only those that can be geocoded AND are valid
        geocoded_locations = []
        for loc in locations:
            coords = self.get_coordinates(loc, text)
            if coords and self.validator.is_valid_location(loc, coords):
                geocoded_locations.append(loc)

        # If no geocoded results and online fallback enabled, try extracting without DB filter
        if not geocoded_locations and allow_online_fallback:
            online_locations = self._extract_unfiltered_locations(text)
            for loc in online_locations:
                if loc.lower() not in [l.lower() for l in locations]:  # Skip already tried
                    coords = self.get_coordinates(loc, text)
                    if coords and self.validator.is_valid_location(loc, coords):
                        geocoded_locations.append(loc)
                        break  # Stop after finding one online location

        features['locations_found'] = len(geocoded_locations)
        if not geocoded_locations:
            return features

        features['location_names'] = ', '.join(geocoded_locations)
        primary = geocoded_locations[0]
        features['primary_location'] = primary
        coords = self.get_coordinates(primary, text)
        if coords:
            features['primary_lat'] = coords['lat']
            features['primary_lon'] = coords['lon']
            features['primary_state'] = coords.get('state', '')

            # Add confidence validation for the primary location
            validation_result = self.validator.validate_with_confidence(primary, coords)
            features['validation_confidence'] = validation_result['confidence']
            features['validation_reasons'] = '; '.join(validation_result['reasons'])
            features['is_valid_location'] = int(validation_result['is_valid'])

            loc_type = coords.get('type', '')
            features['is_international'] = int(loc_type == 'international')
            features['is_regional'] = int(loc_type == 'regional')
            features['is_major_city'] = int(loc_type == 'city')

            distance = self.calculate_distance(
                self.reference['lat'], self.reference['lon'],
                coords['lat'], coords['lon']
            )
            features['distance_from_ref_km'] = round(distance, 2)

            travel_type = 'flight' if distance > 500 or features['is_international'] else 'car'
            features['estimated_travel_hours'] = round(self.estimate_travel_time(distance, travel_type), 2)

            features['is_local'] = int(distance <= 100)
            features['is_remote'] = int(distance > 500)
            features['is_interstate'] = int(coords.get('state', 'NSW') != 'NSW' and not features['is_international'])

            if features['is_international']:
                features['travel_category'] = 'international'
            elif features['is_remote']:
                features['travel_category'] = 'remote'
            elif features['is_interstate']:
                features['travel_category'] = 'interstate'
            elif features['is_regional']:
                features['travel_category'] = 'regional'
            elif features['is_local']:
                features['travel_category'] = 'local'
            else:
                features['travel_category'] = 'domestic'

        return features
