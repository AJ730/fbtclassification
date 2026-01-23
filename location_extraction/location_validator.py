"""
Location validation for filtering implausible and out-of-Australia matches.
"""
from typing import Optional, Dict

# Australian states and territories
AUSTRALIAN_STATES = {
    'NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'NT', 'ACT', 'AUS', 'AUSTRALIA'
}

# Valid location types
VALID_LOCATION_TYPES = {
    'city', 'regional', 'suburb', 'restaurant', 'cafe', 'hotel', 
    'venue', 'airport', 'international'
}

# Likely international keywords that indicate out-of-Australia locations
INTERNATIONAL_INDICATORS = {
    'london', 'paris', 'new york', 'tokyo', 'bangkok', 'dubai', 'singapore',
    'hong kong', 'toronto', 'vancouver', 'los angeles', 'san francisco',
    'mexico', 'buenos aires', 'rio', 'shanghai', 'mumbai', 'delhi',
    'berlin', 'amsterdam', 'zurich', 'auckland', 'fiji', 'bali',
    'phuket', 'chiang mai', 'hanoi', 'ho chi minh'
}

# Implausible patterns (likely false positives)
IMPLAUSIBLE_PATTERNS = {
    'and', 'the', 'or', 'a', 'at', 'to', 'from', 'for', 'with',
    'inc', 'pty', 'ltd', 'co', 'group', 'services', 'solutions',
    'business', 'industries', 'corporation', 'company', 'australia pty',
    'australia limited', 'trading as', 'proprietary', 'limited',
    'consulting', 'advisory', 'management', 'systems', 'technology',
    'australia', 'pty ltd', 'p/l', 'no liability'
}

# Business name indicators (likely not locations)
BUSINESS_INDICATORS = {
    'restaurant', 'cafe', 'hotel', 'bar', 'pub', 'club', 'lounge',
    'shop', 'store', 'market', 'plaza', 'mall',
    'office', 'building', 'tower', 'house', 'place', 'court',
    'street', 'road', 'avenue', 'lane', 'way', 'drive', 'close',
    'services', 'consulting', 'advisory', 'management', 'systems',
    'technology', 'software', 'digital', 'media', 'marketing',
    'finance', 'banking', 'insurance', 'legal', 'accounting',
    'engineering', 'construction', 'property', 'real estate',
    'health', 'medical', 'dental', 'pharmacy', 'fitness', 'gym',
    'travel', 'tourism', 'agency', 'bureau', 'centre', 'center'
}

# State-specific coordinate bounds for more precise validation
STATE_BOUNDS = {
    'NSW': {'lat_min': -37.5, 'lat_max': -28.0, 'lon_min': 140.0, 'lon_max': 154.0},
    'VIC': {'lat_min': -39.0, 'lat_max': -34.0, 'lon_min': 140.0, 'lon_max': 150.0},
    'QLD': {'lat_min': -29.0, 'lat_max': -10.0, 'lon_min': 137.0, 'lon_max': 154.0},
    'WA': {'lat_min': -35.0, 'lat_max': -13.0, 'lon_min': 112.0, 'lon_max': 129.0},
    'SA': {'lat_min': -38.0, 'lat_max': -26.0, 'lon_min': 129.0, 'lon_max': 141.0},
    'TAS': {'lat_min': -43.5, 'lat_max': -39.5, 'lon_min': 143.0, 'lon_max': 148.5},
    'NT': {'lat_min': -26.0, 'lat_max': -10.0, 'lon_min': 129.0, 'lon_max': 138.0},
    'ACT': {'lat_min': -35.9, 'lat_max': -35.1, 'lon_min': 148.7, 'lon_max': 149.4}
}

# Common location name patterns (regex)
LOCATION_PATTERNS = [
    r'^\w+ (cbd|city|centre|center)$',  # "Sydney CBD", "Melbourne City"
    r'^\w+ (beach|bay|harbour|harbor)$',  # "Bondi Beach", "Sydney Harbour"
    r'^\w+ (airport|station|terminal)$',  # "Sydney Airport"
    r'^\w+ (hotel|motel|inn)$',  # "Sydney Hotel"
    r'^\w+ (restaurant|cafe|bar)$',  # "Sydney Restaurant"
]

# Minimum confidence scores for different validation checks
CONFIDENCE_THRESHOLDS = {
    'database_match': 1.0,  # Exact database match
    'state_coords_match': 0.9,  # Coordinates match claimed state
    'australia_bounds': 0.7,  # Within Australia but state unknown
    'pattern_match': 0.6,  # Matches location pattern
    'length_valid': 0.5,  # Meets minimum length
    'no_business_indicators': 0.4,  # No business keywords
    'no_implausible': 0.3,  # No implausible patterns
    'no_international': 0.2,  # No international indicators
}

# Minimum location name length
MIN_LOCATION_LENGTH = 3


class LocationValidator:
    """Validates extracted locations for plausibility and Australian origin."""
    
    def __init__(self, australian_locations_db: Optional[Dict] = None):
        """
        Initialize validator.
        
        Args:
            australian_locations_db: Dictionary of known Australian locations
        """
        self.db = australian_locations_db or {}
        self.db_keys = {k.lower() for k in self.db.keys()}
        
        # Create reverse mapping for state validation
        self.state_locations = {}
        for loc_name, loc_data in self.db.items():
            state = loc_data.get('state', '').upper()
            if state:
                if state not in self.state_locations:
                    self.state_locations[state] = set()
                self.state_locations[state].add(loc_name.lower())
    
    def is_valid_location(self, location_name: str, coords: Optional[Dict] = None) -> bool:
        """
        Validate if a location is plausible and Australian.
        
        Args:
            location_name: The location name to validate
            coords: Optional coordinates dict with 'lat', 'lon', 'state', 'type' keys
            
        Returns:
            True if location passes validation, False otherwise
        """
        if not location_name:
            return False
        
        loc_lower = location_name.lower().strip()
        
        # Check if in database (highest confidence)
        if loc_lower in self.db_keys:
            return True
        
        # Check if it's in known implausible patterns
        if loc_lower in IMPLAUSIBLE_PATTERNS:
            return False
        
        # Check if it's an international location
        if self._is_international(loc_lower):
            return False
        
        # Check for business name indicators (likely not locations)
        if self._is_business_name(loc_lower):
            return False
        
        # Validate coordinates if provided
        if coords:
            if not self._is_australia_coords(coords):
                return False
            
            # Check if coordinates match claimed state
            if not self._coords_match_state(coords):
                return False
        
        # Check length
        if len(loc_lower) < MIN_LOCATION_LENGTH:
            return False
        
        # Check for valid state
        if coords and 'state' in coords:
            if coords['state'] not in AUSTRALIAN_STATES:
                return False
        
        # Check if it's marked as international in type
        if coords and 'type' in coords and coords['type'] == 'international':
            return False
        
        # Check if it matches common location patterns
        if not self._matches_location_pattern(loc_lower):
            return False
        
        return True
    
    def validate_with_confidence(self, location_name: str, coords: Optional[Dict] = None) -> Dict:
        """
        Validate location and return confidence score with detailed reasoning.
        
        Args:
            location_name: The location name to validate
            coords: Optional coordinates dict
            
        Returns:
            Dict with 'is_valid', 'confidence', and 'reasons' keys
        """
        if not location_name:
            return {'is_valid': False, 'confidence': 0.0, 'reasons': ['Empty location name']}
        
        loc_lower = location_name.lower().strip()
        confidence = 0.0
        reasons = []
        
        # Database match (highest confidence)
        if loc_lower in self.db_keys:
            confidence = CONFIDENCE_THRESHOLDS['database_match']
            reasons.append('Found in Australian locations database')
        
        # Check implausible patterns
        if loc_lower in IMPLAUSIBLE_PATTERNS:
            confidence = 0.0
            reasons.append('Contains implausible pattern')
            return {'is_valid': False, 'confidence': confidence, 'reasons': reasons}
        
        # Check international indicators
        if self._is_international(loc_lower):
            confidence = 0.0
            reasons.append('Contains international location indicators')
            return {'is_valid': False, 'confidence': confidence, 'reasons': reasons}
        
        # Check business name indicators
        if self._is_business_name(loc_lower):
            confidence = max(confidence - 0.3, 0.0)
            reasons.append('Contains business name indicators')
        
        # Coordinate validation
        if coords:
            if self._is_australia_coords(coords):
                confidence = max(confidence, CONFIDENCE_THRESHOLDS['australia_bounds'])
                reasons.append('Coordinates within Australian bounds')
                
                if self._coords_match_state(coords):
                    confidence = max(confidence, CONFIDENCE_THRESHOLDS['state_coords_match'])
                    reasons.append('Coordinates match claimed state')
                else:
                    confidence = min(confidence, CONFIDENCE_THRESHOLDS['australia_bounds'])
                    reasons.append('Coordinates do not match claimed state')
            else:
                confidence = 0.0
                reasons.append('Coordinates outside Australian bounds')
                return {'is_valid': False, 'confidence': confidence, 'reasons': reasons}
        
        # Length validation
        if len(loc_lower) >= MIN_LOCATION_LENGTH:
            confidence = max(confidence, CONFIDENCE_THRESHOLDS['length_valid'])
            reasons.append('Meets minimum length requirement')
        else:
            confidence = min(confidence, 0.1)
            reasons.append('Below minimum length')
        
        # Pattern matching
        if self._matches_location_pattern(loc_lower):
            confidence = max(confidence, CONFIDENCE_THRESHOLDS['pattern_match'])
            reasons.append('Matches location name pattern')
        
        # State validation
        if coords and 'state' in coords:
            if coords['state'] in AUSTRALIAN_STATES:
                reasons.append('Valid Australian state/territory')
            else:
                confidence = 0.0
                reasons.append('Invalid state/territory code')
                return {'is_valid': False, 'confidence': confidence, 'reasons': reasons}
        
        # Type validation
        if coords and 'type' in coords:
            if coords['type'] == 'international':
                confidence = 0.0
                reasons.append('Marked as international location')
                return {'is_valid': False, 'confidence': confidence, 'reasons': reasons}
        
        is_valid = confidence > 0.5  # Require >50% confidence
        return {'is_valid': is_valid, 'confidence': confidence, 'reasons': reasons}
    
    def filter_locations(self, locations: list, coords_dict: Optional[Dict[str, Dict]] = None) -> list:
        """
        Filter list of locations, removing implausible and international ones.
        
        Args:
            locations: List of location names
            coords_dict: Optional dict mapping location names to their coordinates
            
        Returns:
            Filtered list of valid locations
        """
        valid = []
        for loc in locations:
            coords = coords_dict.get(loc) if coords_dict else None
            if self.is_valid_location(loc, coords):
                valid.append(loc)
        return valid
    
    def _is_international(self, location_lower: str) -> bool:
        """Check if location name suggests international location."""
        for intl_indicator in INTERNATIONAL_INDICATORS:
            if intl_indicator in location_lower:
                return True
        return False
    
    def _is_business_name(self, location_lower: str) -> bool:
        """Check if location name contains business indicators."""
        for business_indicator in BUSINESS_INDICATORS:
            if business_indicator in location_lower:
                return True
        return False
    
    def _is_australia_coords(self, coords: Dict) -> bool:
        """
        Validate coordinates are within Australia's geographic bounds.
        
        Australia rough bounds:
        - Latitude: -44 to -10
        - Longitude: 113 to 154
        """
        if 'lat' not in coords or 'lon' not in coords:
            return False
        
        lat = coords.get('lat')
        lon = coords.get('lon')
        
        if lat is None or lon is None:
            return False
        
        # Check if within Australia's approximate bounds
        if -44 <= lat <= -10 and 113 <= lon <= 154:
            return True
        
        return False
    
    def _coords_match_state(self, coords: Dict) -> bool:
        """
        Check if coordinates are within the bounds of the claimed state.
        
        Args:
            coords: Dict with 'lat', 'lon', 'state' keys
            
        Returns:
            True if coordinates are plausible for the claimed state
        """
        if 'state' not in coords or 'lat' not in coords or 'lon' not in coords:
            return True  # Can't validate, assume valid
        
        state = coords['state'].upper()
        lat = coords['lat']
        lon = coords['lon']
        
        if state not in STATE_BOUNDS:
            return True  # Unknown state, assume valid
        
        bounds = STATE_BOUNDS[state]
        if (bounds['lat_min'] <= lat <= bounds['lat_max'] and 
            bounds['lon_min'] <= lon <= bounds['lon_max']):
            return True
        
        return False
    
    def _matches_location_pattern(self, location_lower: str) -> bool:
        """
        Check if location name matches common location patterns.
        
        Args:
            location_lower: Lowercase location name
            
        Returns:
            True if matches a valid location pattern
        """
        import re
        
        # Check against known location patterns
        for pattern in LOCATION_PATTERNS:
            if re.match(pattern, location_lower):
                return True
        
        # Additional heuristics
        words = location_lower.split()
        
        # Multi-word locations are generally more plausible
        if len(words) >= 2:
            return True
        
        # Single words that are long enough and don't contain business indicators
        if len(location_lower) >= 4 and not self._is_business_name(location_lower):
            return True
        
        # Known location suffixes
        location_suffixes = ['ton', 'ville', 'burg', 'field', 'hill', 'wood', 'brook', 'vale', 'bay', 'beach']
        for suffix in location_suffixes:
            if location_lower.endswith(suffix):
                return True
        
        return False
