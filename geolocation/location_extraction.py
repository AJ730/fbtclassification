"""
Location extraction and geocoding utilities for the FBT pipeline.
Extracted from notebook to enable reuse across modules.
"""
import math
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Geocoding
try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    from geopy.exc import GeocoderTimedOut
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("Note: geopy not installed. Run: pip install geopy")

try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except Exception:
    GEOPY_AVAILABLE = False

from .location_db import AUSTRALIAN_LOCATIONS

CONFIG = {
    # Reference location for distance calculations (Sydney CBD - Rabobank office)
    'reference_location': {'lat': -33.8688, 'lon': 151.2093, 'name': 'Sydney CBD'},

    # Enable/disable features
    'enable_geocoding': True,
}

class LocationExtractor:
    """
    Extract and geocode locations from expense descriptions.
    """
    
    def __init__(self, reference_location: Dict = None):
        self.locations_db = AUSTRALIAN_LOCATIONS
        self.reference = reference_location or CONFIG['reference_location']
        self.cache = {}
        
        # Build pattern for location matching
        location_names = sorted(self.locations_db.keys(), key=len, reverse=True)
        escaped_names = [re.escape(name) for name in location_names]
        self.location_pattern = re.compile(
            r'\b(' + '|'.join(escaped_names) + r')\b',
            re.IGNORECASE
        )
        
        # Initialize geocoder for unknown locations (if available)
        if GEOPY_AVAILABLE:
            self.geocoder = Nominatim(user_agent="fbt_classifier")
        else:
            self.geocoder = None
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract location names from text.
        """
        if pd.isna(text) or not text:
            return []
        
        text = str(text).lower()
        matches = self.location_pattern.findall(text)
        return list(set(matches))
    
    def get_coordinates(self, location_name: str) -> Optional[Dict]:
        """
        Get coordinates for a location name.
        """
        location_name = location_name.lower().strip()
        
        # Check cache first
        if location_name in self.cache:
            return self.cache[location_name]
        
        # Check database
        if location_name in self.locations_db:
            coords = self.locations_db[location_name]
            self.cache[location_name] = coords
            return coords
        
        # Try geocoding unknown locations (with rate limiting)
        if self.geocoder and CONFIG.get('enable_geocoding', False):
            try:
                result = self.geocoder.geocode(f"{location_name}, Australia", timeout=5)
                if result:
                    coords = {'lat': result.latitude, 'lon': result.longitude, 
                              'state': 'UNKNOWN', 'type': 'geocoded'}
                    self.cache[location_name] = coords
                    return coords
            except Exception:
                pass
        
        return None
    
    def calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def estimate_travel_time(self, distance_km: float, travel_type: str = 'auto') -> float:
        """
        Estimate travel time in hours based on distance.
        """
        if distance_km <= 0:
            return 0
        
        # Rough estimates
        if travel_type == 'flight' or distance_km > 500:
            # Flight time estimate (800 km/h average + 2h airport time)
            return (distance_km / 800) + 2
        elif travel_type == 'car' or distance_km <= 500:
            # Driving estimate (80 km/h average including stops)
            return distance_km / 80
        else:
            # Default to car
            return distance_km / 80
    
    def extract_location_features(self, text: str) -> Dict:
        """
        Extract all location-related features from text.
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
            'is_local': 0,  # Within 100km
            'is_interstate': 0,
            'is_remote': 0,  # > 500km
            'travel_category': 'unknown'
        }
        
        locations = self.extract_locations(text)
        features['locations_found'] = len(locations)
        if not locations:
            return features
        
        features['location_names'] = ', '.join(locations)
        
        # Use first found location as primary
        primary = locations[0]
        features['primary_location'] = primary
        
        coords = self.get_coordinates(primary)
        if coords:
            features['primary_lat'] = coords['lat']
            features['primary_lon'] = coords['lon']
            features['primary_state'] = coords.get('state', '')
            
            # Location type flags
            loc_type = coords.get('type', '')
            features['is_international'] = int(loc_type == 'international')
            features['is_regional'] = int(loc_type == 'regional')
            features['is_major_city'] = int(loc_type == 'city')
            
            # Calculate distance from reference
            distance = self.calculate_distance(
                self.reference['lat'], self.reference['lon'],
                coords['lat'], coords['lon']
            )
            features['distance_from_ref_km'] = round(distance, 2)
            
            # Travel time estimate
            travel_type = 'flight' if distance > 500 or features['is_international'] else 'car'
            features['estimated_travel_hours'] = round(
                self.estimate_travel_time(distance, travel_type), 2
            )
            
            # Distance categories
            features['is_local'] = int(distance <= 100)
            features['is_remote'] = int(distance > 500)
            features['is_interstate'] = int(
                coords.get('state', 'NSW') != 'NSW' and not features['is_international']
            )
            
            # Travel category
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