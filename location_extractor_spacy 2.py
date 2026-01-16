import json
import logging
import math
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

import pandas as pd
import pycountry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# GEONAMES CITIES DATABASE
# Uses cities15000 data structure - cities with population > 15,000
# =============================================================================

class GeoNamesCities:
    """
    Local cache of major world cities for fast disambiguation.

    Based on GeoNames cities15000 dataset structure.
    We store a curated subset for common disambiguation cases.
    """

    # Feature code priority (higher = more important)
    FEATURE_PRIORITY = {
        'PPLC': 100,   # Capital of a political entity
        'PPLA': 90,    # Seat of first-order admin division
        'PPLA2': 80,   # Seat of second-order admin division
        'PPLA3': 70,   # Seat of third-order admin division
        'PPLA4': 60,   # Seat of fourth-order admin division
        'PPL': 50,     # Populated place
        'PPLX': 40,    # Section of populated place
        'PPLL': 30,    # Populated locality
        'PPLG': 20,    # Seat of government
    }

    def __init__(self, cache_file: str = 'geonames_cities_cache.json'):
        self.cache_file = Path(cache_file)
        self.cities = self._load_or_build_cache()

    def _load_or_build_cache(self) -> Dict:
        """Load cached cities or build from embedded data."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} cities from cache")
                    return data
            except:
                pass

        # Build embedded major cities database
        cities = self._build_major_cities()

        # Save cache
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cities, f, ensure_ascii=False)

        logger.info(f"Built cities database with {len(cities)} entries")
        return cities

    def _build_major_cities(self) -> Dict:
        """
        Build database of major world cities.

        Format: {
            'city_name_lower': [
                {
                    'name': 'London',
                    'country_code': 'GB',
                    'population': 8982000,
                    'feature_code': 'PPLC',
                    'lat': 51.5074,
                    'lon': -0.1278,
                    'admin1': 'England',
                    'score': computed_score
                },
                ...
            ]
        }
        """
        # Major world cities with population data
        # This is a curated subset - in production, load from cities15000.txt
        cities_data = [
            # Format: (name, country, population, feature_code, lat, lon, admin1)

            # === MEGA CITIES (10M+) ===
            ('Tokyo', 'JP', 37400000, 'PPLC', 35.6762, 139.6503, 'Tokyo'),
            ('Delhi', 'IN', 31181000, 'PPLC', 28.6139, 77.2090, 'Delhi'),
            ('Shanghai', 'CN', 27796000, 'PPLA', 31.2304, 121.4737, 'Shanghai'),
            ('São Paulo', 'BR', 22430000, 'PPLA', -23.5505, -46.6333, 'São Paulo'),
            ('Mexico City', 'MX', 21919000, 'PPLC', 19.4326, -99.1332, 'Mexico City'),
            ('Cairo', 'EG', 21323000, 'PPLC', 30.0444, 31.2357, 'Cairo'),
            ('Mumbai', 'IN', 20961000, 'PPLA', 19.0760, 72.8777, 'Maharashtra'),
            ('Beijing', 'CN', 20896000, 'PPLC', 39.9042, 116.4074, 'Beijing'),
            ('Dhaka', 'BD', 17081000, 'PPLC', 23.8103, 90.4125, 'Dhaka'),
            ('Osaka', 'JP', 19111000, 'PPLA', 34.6937, 135.5023, 'Osaka'),
            ('New York', 'US', 18713220, 'PPL', 40.7128, -74.0060, 'New York'),
            ('Karachi', 'PK', 16459000, 'PPLA', 24.8607, 67.0011, 'Sindh'),
            ('Buenos Aires', 'AR', 15369000, 'PPLC', -34.6037, -58.3816, 'Buenos Aires'),
            ('Chongqing', 'CN', 15354000, 'PPLA', 29.4316, 106.9123, 'Chongqing'),
            ('Istanbul', 'TR', 15415000, 'PPLA', 41.0082, 28.9784, 'Istanbul'),
            ('Kolkata', 'IN', 14974000, 'PPLA', 22.5726, 88.3639, 'West Bengal'),
            ('Lagos', 'NG', 14368000, 'PPLA', 6.5244, 3.3792, 'Lagos'),
            ('Manila', 'PH', 14158000, 'PPLC', 14.5995, 120.9842, 'Metro Manila'),
            ('Rio de Janeiro', 'BR', 13634000, 'PPLA', -22.9068, -43.1729, 'Rio de Janeiro'),
            ('Guangzhou', 'CN', 13501000, 'PPLA', 23.1291, 113.2644, 'Guangdong'),
            ('Los Angeles', 'US', 12459000, 'PPL', 34.0522, -118.2437, 'California'),
            ('Moscow', 'RU', 12593000, 'PPLC', 55.7558, 37.6173, 'Moscow'),
            ('Shenzhen', 'CN', 12357000, 'PPLA2', 22.5431, 114.0579, 'Guangdong'),
            ('Paris', 'FR', 11017000, 'PPLC', 48.8566, 2.3522, 'Île-de-France'),
            ('Jakarta', 'ID', 10915000, 'PPLC', -6.2088, 106.8456, 'Jakarta'),
            ('London', 'GB', 8982000, 'PPLC', 51.5074, -0.1278, 'England'),
            ('Lima', 'PE', 10883000, 'PPLC', -12.0464, -77.0428, 'Lima'),
            ('Bangkok', 'TH', 10539000, 'PPLC', 13.7563, 100.5018, 'Bangkok'),
            ('Seoul', 'KR', 9776000, 'PPLC', 37.5665, 126.9780, 'Seoul'),
            ('Nagoya', 'JP', 9113000, 'PPLA', 35.1815, 136.9066, 'Aichi'),

            # === MAJOR CITIES (1M-10M) ===
            ('Chicago', 'US', 8865000, 'PPL', 41.8781, -87.6298, 'Illinois'),
            ('Ho Chi Minh City', 'VN', 8993000, 'PPLA', 10.8231, 106.6297, 'Ho Chi Minh'),
            ('Hong Kong', 'HK', 7500700, 'PPLC', 22.3193, 114.1694, 'Hong Kong'),
            ('Singapore', 'SG', 5850342, 'PPLC', 1.3521, 103.8198, 'Singapore'),
            ('Riyadh', 'SA', 7676654, 'PPLC', 24.7136, 46.6753, 'Riyadh'),
            ('Kuala Lumpur', 'MY', 7564000, 'PPLC', 3.1390, 101.6869, 'Kuala Lumpur'),
            ('Toronto', 'CA', 6417516, 'PPLA', 43.6532, -79.3832, 'Ontario'),
            ('Santiago', 'CL', 6680000, 'PPLC', -33.4489, -70.6693, 'Santiago'),
            ('Madrid', 'ES', 6642000, 'PPLC', 40.4168, -3.7038, 'Madrid'),
            ('Miami', 'US', 6166488, 'PPL', 25.7617, -80.1918, 'Florida'),
            ('Dallas', 'US', 5743938, 'PPL', 32.7767, -96.7970, 'Texas'),
            ('Philadelphia', 'US', 5649300, 'PPL', 39.9526, -75.1652, 'Pennsylvania'),
            ('Houston', 'US', 5464251, 'PPL', 29.7604, -95.3698, 'Texas'),
            ('Atlanta', 'US', 5286728, 'PPL', 33.7490, -84.3880, 'Georgia'),
            ('Washington', 'US', 5207627, 'PPLC', 38.9072, -77.0369, 'District of Columbia'),
            ('Johannesburg', 'ZA', 5635127, 'PPLA', -26.2041, 28.0473, 'Gauteng'),
            ('Barcelona', 'ES', 5575000, 'PPLA', 41.3851, 2.1734, 'Catalonia'),
            ('Sydney', 'AU', 5312163, 'PPLA', -33.8688, 151.2093, 'New South Wales'),
            ('Melbourne', 'AU', 5078193, 'PPLA', -37.8136, 144.9631, 'Victoria'),
            ('Nairobi', 'KE', 4735000, 'PPLC', -1.2921, 36.8219, 'Nairobi'),
            ('Berlin', 'DE', 3669491, 'PPLC', 52.5200, 13.4050, 'Berlin'),
            ('Rome', 'IT', 4342212, 'PPLC', 41.9028, 12.4964, 'Lazio'),
            ('Dubai', 'AE', 3478300, 'PPLA', 25.2048, 55.2708, 'Dubai'),
            ('Abu Dhabi', 'AE', 1483000, 'PPLC', 24.4539, 54.3773, 'Abu Dhabi'),
            ('Addis Ababa', 'ET', 3604000, 'PPLC', 8.9806, 38.7578, 'Addis Ababa'),
            ('Boston', 'US', 4628910, 'PPL', 42.3601, -71.0589, 'Massachusetts'),
            ('Phoenix', 'US', 4192887, 'PPL', 33.4484, -112.0740, 'Arizona'),
            ('San Francisco', 'US', 3281212, 'PPL', 37.7749, -122.4194, 'California'),
            ('Seattle', 'US', 3489000, 'PPL', 47.6062, -122.3321, 'Washington'),
            ('Denver', 'US', 2897000, 'PPL', 39.7392, -104.9903, 'Colorado'),
            ('San Diego', 'US', 3298634, 'PPL', 32.7157, -117.1611, 'California'),
            ('Montreal', 'CA', 4221000, 'PPLA', 45.5017, -73.5673, 'Quebec'),
            ('Vancouver', 'CA', 2581000, 'PPLA2', 49.2827, -123.1207, 'British Columbia'),
            ('Munich', 'DE', 1538302, 'PPLA', 48.1351, 11.5820, 'Bavaria'),
            ('Frankfurt', 'DE', 753056, 'PPL', 50.1109, 8.6821, 'Hesse'),
            ('Hamburg', 'DE', 1906411, 'PPLA', 53.5511, 9.9937, 'Hamburg'),
            ('Milan', 'IT', 1378689, 'PPLA', 45.4642, 9.1900, 'Lombardy'),
            ('Naples', 'IT', 959470, 'PPLA', 40.8518, 14.2681, 'Campania'),
            ('Turin', 'IT', 870952, 'PPLA', 45.0703, 7.6869, 'Piedmont'),
            ('Florence', 'IT', 383084, 'PPLA', 43.7696, 11.2558, 'Tuscany'),
            ('Venice', 'IT', 261905, 'PPLA', 45.4408, 12.3155, 'Veneto'),
            ('Lisbon', 'PT', 2942000, 'PPLC', 38.7223, -9.1393, 'Lisbon'),
            ('Amsterdam', 'NL', 1157000, 'PPLC', 52.3676, 4.9041, 'North Holland'),
            ('Brussels', 'BE', 1191604, 'PPLC', 50.8476, 4.3572, 'Brussels'),
            ('Vienna', 'AT', 1929944, 'PPLC', 48.2082, 16.3738, 'Vienna'),
            ('Zurich', 'CH', 415367, 'PPLA', 47.3769, 8.5417, 'Zurich'),
            ('Geneva', 'CH', 201818, 'PPLA', 46.2044, 6.1432, 'Geneva'),
            ('Prague', 'CZ', 1324277, 'PPLC', 50.0755, 14.4378, 'Prague'),
            ('Warsaw', 'PL', 1793579, 'PPLC', 52.2297, 21.0122, 'Masovian'),
            ('Budapest', 'HU', 1759407, 'PPLC', 47.4979, 19.0402, 'Budapest'),
            ('Copenhagen', 'DK', 1346485, 'PPLC', 55.6761, 12.5683, 'Capital Region'),
            ('Stockholm', 'SE', 975904, 'PPLC', 59.3293, 18.0686, 'Stockholm'),
            ('Oslo', 'NO', 693494, 'PPLC', 59.9139, 10.7522, 'Oslo'),
            ('Helsinki', 'FI', 653835, 'PPLC', 60.1699, 24.9384, 'Uusimaa'),
            ('Dublin', 'IE', 1228179, 'PPLC', 53.3498, -6.2603, 'Leinster'),
            ('Edinburgh', 'GB', 488050, 'PPLA', 55.9533, -3.1883, 'Scotland'),
            ('Manchester', 'GB', 545500, 'PPL', 53.4808, -2.2426, 'England'),
            ('Birmingham', 'GB', 1141816, 'PPL', 52.4862, -1.8904, 'England'),
            ('Glasgow', 'GB', 626410, 'PPLA', 55.8642, -4.2518, 'Scotland'),
            ('Liverpool', 'GB', 498042, 'PPL', 53.4084, -2.9916, 'England'),
            ('Athens', 'GR', 3153000, 'PPLC', 37.9838, 23.7275, 'Attica'),
            ('Bucharest', 'RO', 2106144, 'PPLC', 44.4268, 26.1025, 'Bucharest'),
            ('Sofia', 'BG', 1307439, 'PPLC', 42.6977, 23.3219, 'Sofia-City'),
            ('Belgrade', 'RS', 1378682, 'PPLC', 44.7866, 20.4489, 'Belgrade'),
            ('Zagreb', 'HR', 804200, 'PPLC', 45.8150, 15.9819, 'Zagreb'),
            ('Kiev', 'UA', 2884000, 'PPLC', 50.4501, 30.5234, 'Kyiv'),
            ('Kyiv', 'UA', 2884000, 'PPLC', 50.4501, 30.5234, 'Kyiv'),
            ('St. Petersburg', 'RU', 5383890, 'PPLA', 59.9311, 30.3609, 'St. Petersburg'),
            ('Tel Aviv', 'IL', 451523, 'PPL', 32.0853, 34.7818, 'Tel Aviv'),
            ('Jerusalem', 'IL', 919438, 'PPLC', 31.7683, 35.2137, 'Jerusalem'),
            ('Beirut', 'LB', 2424400, 'PPLC', 33.8938, 35.5018, 'Beirut'),
            ('Amman', 'JO', 1812319, 'PPLC', 31.9454, 35.9284, 'Amman'),
            ('Doha', 'QA', 1450000, 'PPLC', 25.2867, 51.5333, 'Doha'),
            ('Kuwait City', 'KW', 60064, 'PPLC', 29.3759, 47.9774, 'Kuwait'),
            ('Muscat', 'OM', 797000, 'PPLC', 23.5880, 58.3829, 'Muscat'),
            ('Tehran', 'IR', 8847000, 'PPLC', 35.6892, 51.3890, 'Tehran'),
            ('Casablanca', 'MA', 3359818, 'PPLA', 33.5731, -7.5898, 'Casablanca-Settat'),
            ('Cape Town', 'ZA', 4618000, 'PPLA', -33.9249, 18.4241, 'Western Cape'),
            ('Auckland', 'NZ', 1657200, 'PPLA', -36.8509, 174.7645, 'Auckland'),
            ('Wellington', 'NZ', 418500, 'PPLC', -41.2924, 174.7787, 'Wellington'),

            # === US CITIES (various sizes) ===
            ('Las Vegas', 'US', 2266715, 'PPL', 36.1699, -115.1398, 'Nevada'),
            ('Orlando', 'US', 2509831, 'PPL', 28.5383, -81.3792, 'Florida'),
            ('Austin', 'US', 1943299, 'PPL', 30.2672, -97.7431, 'Texas'),
            ('Portland', 'US', 2492412, 'PPL', 45.5152, -122.6784, 'Oregon'),
            ('Minneapolis', 'US', 429954, 'PPL', 44.9778, -93.2650, 'Minnesota'),
            ('Detroit', 'US', 670031, 'PPL', 42.3314, -83.0458, 'Michigan'),
            ('Cleveland', 'US', 372624, 'PPL', 41.4993, -81.6944, 'Ohio'),
            ('New Orleans', 'US', 391006, 'PPL', 29.9511, -90.0715, 'Louisiana'),
            ('Nashville', 'US', 692587, 'PPLA', 36.1627, -86.7816, 'Tennessee'),
            ('Salt Lake City', 'US', 200567, 'PPLA', 40.7608, -111.8910, 'Utah'),
            ('Honolulu', 'US', 350964, 'PPLA', 21.3069, -157.8583, 'Hawaii'),
            ('San Jose', 'US', 1013240, 'PPL', 37.3382, -121.8863, 'California'),
            ('Cupertino', 'US', 60170, 'PPL', 37.3230, -122.0322, 'California'),
            ('Palo Alto', 'US', 65364, 'PPL', 37.4419, -122.1430, 'California'),
            ('Mountain View', 'US', 82376, 'PPL', 37.3861, -122.0839, 'California'),
            ('Redmond', 'US', 73256, 'PPL', 47.6740, -122.1215, 'Washington'),
            ('Menlo Park', 'US', 35254, 'PPL', 37.4530, -122.1817, 'California'),
            ('Fremont', 'US', 230504, 'PPL', 37.5485, -121.9886, 'California'),

            # === AUSTRALIAN CITIES ===
            ('Brisbane', 'AU', 2514184, 'PPLA', -27.4698, 153.0251, 'Queensland'),
            ('Perth', 'AU', 2085973, 'PPLA', -31.9505, 115.8605, 'Western Australia'),
            ('Adelaide', 'AU', 1345777, 'PPLA', -34.9285, 138.6007, 'South Australia'),
            ('Gold Coast', 'AU', 679127, 'PPL', -28.0167, 153.4000, 'Queensland'),
            ('Canberra', 'AU', 453558, 'PPLC', -35.2809, 149.1300, 'ACT'),
            ('Newcastle', 'AU', 322278, 'PPL', -32.9283, 151.7817, 'New South Wales'),
            ('Hobart', 'AU', 240342, 'PPLA', -42.8821, 147.3272, 'Tasmania'),
            ('Darwin', 'AU', 147255, 'PPLA', -12.4634, 130.8456, 'Northern Territory'),

            # === ASIAN CITIES ===
            ('Taipei', 'TW', 2646204, 'PPLC', 25.0330, 121.5654, 'Taipei'),
            ('Hanoi', 'VN', 8053663, 'PPLC', 21.0285, 105.8542, 'Hanoi'),
            ('Macau', 'MO', 649335, 'PPLC', 22.1987, 113.5439, 'Macau'),
            ('Phnom Penh', 'KH', 2129371, 'PPLC', 11.5564, 104.9282, 'Phnom Penh'),
            ('Yangon', 'MM', 5160512, 'PPLC', 16.8661, 96.1951, 'Yangon'),
            ('Colombo', 'LK', 752993, 'PPLC', 6.9271, 79.8612, 'Western'),
            ('Kathmandu', 'NP', 1442271, 'PPLC', 27.7172, 85.3240, 'Bagmati'),

            # === EUROPEAN CITIES ===
            ('Nice', 'FR', 343629, 'PPLA2', 43.7102, 7.2620, "Provence-Alpes-Côte d'Azur"),
            ('Lyon', 'FR', 516092, 'PPLA', 45.7640, 4.8357, 'Auvergne-Rhône-Alpes'),
            ('Marseille', 'FR', 870018, 'PPLA', 43.2965, 5.3698, "Provence-Alpes-Côte d'Azur"),
            ('Menton', 'FR', 28833, 'PPL', 43.7747, 7.5006, "Provence-Alpes-Côte d'Azur"),
            ('Girona', 'ES', 101852, 'PPLA2', 41.9794, 2.8214, 'Catalonia'),
            ('Valencia', 'ES', 791413, 'PPLA', 39.4699, -0.3763, 'Valencia'),
            ('Seville', 'ES', 688711, 'PPLA', 37.3891, -5.9845, 'Andalusia'),
            ('Malaga', 'ES', 574654, 'PPLA2', 36.7213, -4.4214, 'Andalusia'),
            ('Modena', 'IT', 186307, 'PPLA3', 44.6471, 10.9252, 'Emilia-Romagna'),
            ('Bologna', 'IT', 392203, 'PPLA', 44.4949, 11.3426, 'Emilia-Romagna'),

            # === AFRICAN CITIES ===
            ('Antananarivo', 'MG', 1275207, 'PPLC', -18.8792, 47.5079, 'Analamanga'),
            ('Ouagadougou', 'BF', 2453496, 'PPLC', 12.3714, -1.5197, 'Centre'),
            ('Accra', 'GH', 2291352, 'PPLC', 5.6037, -0.1870, 'Greater Accra'),
            ('Abidjan', 'CI', 4707000, 'PPLA', 5.3600, -4.0083, 'Abidjan'),

            # === SOUTH AMERICAN CITIES ===
            ('Bogotá', 'CO', 10574000, 'PPLC', 4.7110, -74.0721, 'Bogotá'),
            ('Medellín', 'CO', 2529403, 'PPLA', 6.2442, -75.5812, 'Antioquia'),
            ('Caracas', 'VE', 2935000, 'PPLC', 10.4806, -66.9036, 'Caracas'),
            ('Quito', 'EC', 2011388, 'PPLC', -0.1807, -78.4678, 'Pichincha'),
            ('Montevideo', 'UY', 1319108, 'PPLC', -34.9011, -56.1645, 'Montevideo'),
            ('Asunción', 'PY', 525294, 'PPLC', -25.2637, -57.5759, 'Asunción'),
            ('La Paz', 'BO', 812799, 'PPLC', -16.4897, -68.1193, 'La Paz'),
            ('Potosí', 'BO', 176022, 'PPLA', -19.5836, -65.7531, 'Potosí'),

            # === CENTRAL ASIAN CITIES ===
            ('Ulaanbaatar', 'MN', 1466125, 'PPLC', 47.8864, 106.9057, 'Ulaanbaatar'),
            ('Almaty', 'KZ', 1977011, 'PPLA', 43.2220, 76.8512, 'Almaty'),
            ('Tashkent', 'UZ', 2571668, 'PPLC', 41.2995, 69.2401, 'Tashkent'),

            # === Small but notable places ===
            ('Vladivostok', 'RU', 606561, 'PPLA', 43.1332, 131.9113, 'Primorsky Krai'),

            # === Places that exist in multiple countries (disambiguation needed) ===
            # London, Ontario, Canada
            ('London', 'CA', 383822, 'PPL', 42.9849, -81.2453, 'Ontario'),
            # Paris, Texas, US
            ('Paris', 'US', 24699, 'PPL', 33.6609, -95.5555, 'Texas'),
            # Melbourne, Florida, US
            ('Melbourne', 'US', 83029, 'PPL', 28.0836, -80.6081, 'Florida'),
            # Sydney, Nova Scotia, Canada
            ('Sydney', 'CA', 29904, 'PPL', 46.1368, -60.1942, 'Nova Scotia'),
            # Perth, Scotland
            ('Perth', 'GB', 47430, 'PPL', 56.3950, -3.4308, 'Scotland'),
            # Birmingham, Alabama, US
            ('Birmingham', 'US', 200733, 'PPL', 33.5207, -86.8025, 'Alabama'),
            # Manchester, New Hampshire, US
            ('Manchester', 'US', 115644, 'PPL', 42.9956, -71.4548, 'New Hampshire'),
        ]

        cities = defaultdict(list)

        for name, country, pop, fcode, lat, lon, admin1 in cities_data:
            name_lower = name.lower()

            # Calculate disambiguation score
            pop_score = math.log10(max(pop, 1)) * 10  # Log scale for population
            feature_score = self.FEATURE_PRIORITY.get(fcode, 25)
            total_score = pop_score + feature_score

            cities[name_lower].append({
                'name': name,
                'country_code': country,
                'population': pop,
                'feature_code': fcode,
                'lat': lat,
                'lon': lon,
                'admin1': admin1,
                'score': round(total_score, 2)
            })

        # Sort each city's candidates by score (highest first)
        for name in cities:
            cities[name] = sorted(cities[name], key=lambda x: -x['score'])

        return dict(cities)

    def lookup(self, name: str, country_hint: str = None) -> Optional[Dict]:
        """
        Look up a city with optional country hint for disambiguation.

        Uses population-based ranking when no hint provided.
        """
        name_lower = name.lower().strip()

        if name_lower not in self.cities:
            return None

        candidates = self.cities[name_lower]

        if not candidates:
            return None

        # If country hint provided, prefer that country
        if country_hint:
            country_upper = country_hint.upper()
            for c in candidates:
                if c['country_code'] == country_upper:
                    return c

        # Return highest-scored candidate (highest population + feature importance)
        return candidates[0]

    def get_all_candidates(self, name: str) -> List[Dict]:
        """Get all candidates for a place name."""
        name_lower = name.lower().strip()
        return self.cities.get(name_lower, [])

    def exists(self, name: str) -> bool:
        """Check if a place name exists in database."""
        return name.lower().strip() in self.cities


# =============================================================================
# COUNTRY DETECTOR (Using pycountry)
# =============================================================================

class CountryDetector:
    """Detect country from text using pycountry library."""

    def __init__(self):
        self._build_lookups()

    def _build_lookups(self):
        """Build country name → code lookups from pycountry."""
        self.name_to_code = {}
        self.code_to_name = {}

        # Official names from pycountry
        for country in pycountry.countries:
            code = country.alpha_2.lower()
            self.name_to_code[country.name.lower()] = code
            self.code_to_name[code] = country.name

            if hasattr(country, 'common_name'):
                self.name_to_code[country.common_name.lower()] = code
            if hasattr(country, 'official_name'):
                self.name_to_code[country.official_name.lower()] = code
            self.name_to_code[country.alpha_3.lower()] = code

        # Demonyms
        self.demonyms = {
            'australian': 'au', 'american': 'us', 'canadian': 'ca', 'british': 'gb',
            'english': 'gb', 'scottish': 'gb', 'welsh': 'gb', 'irish': 'ie',
            'french': 'fr', 'german': 'de', 'italian': 'it', 'spanish': 'es',
            'portuguese': 'pt', 'dutch': 'nl', 'belgian': 'be', 'swiss': 'ch',
            'austrian': 'at', 'polish': 'pl', 'czech': 'cz', 'hungarian': 'hu',
            'romanian': 'ro', 'bulgarian': 'bg', 'greek': 'gr', 'turkish': 'tr',
            'russian': 'ru', 'ukrainian': 'ua', 'swedish': 'se', 'norwegian': 'no',
            'danish': 'dk', 'finnish': 'fi', 'japanese': 'jp', 'chinese': 'cn',
            'korean': 'kr', 'taiwanese': 'tw', 'thai': 'th', 'vietnamese': 'vn',
            'indonesian': 'id', 'malaysian': 'my', 'singaporean': 'sg', 'filipino': 'ph',
            'indian': 'in', 'pakistani': 'pk', 'bangladeshi': 'bd', 'nepalese': 'np',
            'sri lankan': 'lk', 'srilankan': 'lk', 'lankan': 'lk',
            'iranian': 'ir', 'iraqi': 'iq', 'saudi': 'sa', 'emirati': 'ae',
            'israeli': 'il', 'lebanese': 'lb', 'egyptian': 'eg', 'moroccan': 'ma',
            'nigerian': 'ng', 'kenyan': 'ke', 'ethiopian': 'et', 'south african': 'za',
            'brazilian': 'br', 'mexican': 'mx', 'argentinian': 'ar', 'colombian': 'co',
            'peruvian': 'pe', 'chilean': 'cl', 'venezuelan': 've',
            'kiwi': 'nz', 'aussie': 'au',
        }
        self.name_to_code.update(self.demonyms)

        # Common alternatives
        alternatives = {
            'usa': 'us', 'uk': 'gb', 'uae': 'ae', 'prc': 'cn',
            'holland': 'nl', 'burma': 'mm', 'persia': 'ir',
            'ceylon': 'lk', 'formosa': 'tw', 'czechia': 'cz',
            'ivory coast': 'ci', 'hong kong': 'hk', 'macau': 'mo',
            'phillipines': 'ph', 'philipines': 'ph', 'phillippines': 'ph',
            'srilanka': 'lk', 'sri-lanka': 'lk',
            'england': 'gb', 'scotland': 'gb', 'wales': 'gb',
        }
        self.name_to_code.update(alternatives)

        # Australian states
        self.au_states = {
            'qld': 'Queensland', 'nsw': 'New South Wales', 'vic': 'Victoria',
            'sa': 'South Australia', 'wa': 'Western Australia', 'tas': 'Tasmania',
            'nt': 'Northern Territory', 'act': 'Australian Capital Territory',
            'queensland': 'Queensland', 'new south wales': 'New South Wales',
            'victoria': 'Victoria',
        }

    def is_country_name(self, name: str) -> bool:
        """Check if name is a country."""
        if not name:
            return False
        return name.lower().strip() in self.name_to_code

    def is_demonym(self, word: str) -> bool:
        """Check if word is a demonym."""
        return word.lower().strip() in self.demonyms

    def detect_country(self, text: str) -> Optional[str]:
        """Detect country code from text."""
        if not text:
            return None
        text_lower = text.lower()
        matches = []
        for name, code in self.name_to_code.items():
            if len(name) < 3:
                continue
            pattern = r'\b' + re.escape(name) + r'\b'
            if re.search(pattern, text_lower):
                matches.append((name, code, len(name)))
        if matches:
            matches.sort(key=lambda x: -x[2])
            return matches[0][1]
        return None

    def detect_au_state(self, text: str) -> Optional[str]:
        """Detect Australian state from text."""
        if not text:
            return None
        text_lower = text.lower()
        for code, name in self.au_states.items():
            pattern = r'\b' + re.escape(code) + r'\b'
            if re.search(pattern, text_lower):
                return name
        return None

    def get_country_name(self, code: str) -> Optional[str]:
        """Get country name from code."""
        if not code:
            return None
        code_lower = code.lower()
        return self.code_to_name.get(code_lower)


# =============================================================================
# SPACY NER WITH CONTEXTUAL SCORING
# =============================================================================

class SpacyNER:
    """Extract locations using spaCy with context-aware scoring."""

    BLACKLIST = {
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'at', 'to', 'from', 'in', 'on', 'for', 'with', 'the', 'a', 'an',
        'pty', 'ltd', 'inc', 'corp', 'llc',
        # Company names that get misidentified as locations
        'amazon', 'apple', 'google', 'microsoft', 'meta', 'tesla', 'nvidia',
        'uber', 'lyft', 'airbnb', 'netflix', 'spotify', 'adobe', 'oracle',
        'salesforce', 'ibm', 'intel', 'cisco', 'dell', 'hp', 'samsung',
        'qantas', 'emirates', 'cathay', 'lufthansa', 'delta', 'united',
    }

    VENUE_WORDS = {
        'cafe', 'café', 'restaurant', 'bar', 'pub', 'grill', 'kitchen',
        'bistro', 'brasserie', 'trattoria', 'pizzeria', 'diner', 'tavern',
        'club', 'lounge', 'inn', 'hotel', 'motel', 'resort', 'hostel',
        'steakhouse', 'chophouse', 'bbq', 'bakery', 'deli',
    }

    LOCATION_PREPOSITIONS = {'in', 'at', 'to', 'from', 'near', 'around', 'visit', 'visiting'}

    def __init__(self, model_name: str = None):
        import spacy

        models = [model_name] if model_name else [
            'en_core_web_trf', 'en_core_web_lg', 'en_core_web_md', 'en_core_web_sm'
        ]

        self.nlp = None
        for model in models:
            if not model:
                continue
            try:
                self.nlp = spacy.load(model)
                logger.info(f"Loaded spaCy model: {model}")
                break
            except OSError:
                continue

        if not self.nlp:
            raise RuntimeError("No spaCy model found")

        self.country_detector = CountryDetector()
        self.cities_db = GeoNamesCities()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better NER."""
        if not text:
            return text
        words = text.split()
        normalized = []
        for word in words:
            word_clean = word.strip('.,;:!?()[]{}"\'-')
            if (word_clean.islower() and len(word_clean) >= 3 and
                    word_clean.lower() not in self.BLACKLIST and
                    word_clean.lower() not in self.VENUE_WORDS):
                normalized.append(word_clean.title())
            else:
                normalized.append(word)
        return ' '.join(normalized)

    def _score_entity(self, entity: Dict, text: str, all_entities: List[Dict]) -> float:
        """Score entity based on contextual signals."""
        score = entity.get('confidence', 0.5)
        text_lower = text.lower()
        entity_lower = entity['word'].lower()

        # Check if in GeoNames database (trusted source)
        if self.cities_db.exists(entity['word']):
            score += 0.25

            # Get population-based boost
            city_info = self.cities_db.lookup(entity['word'])
            if city_info:
                pop = city_info.get('population', 0)
                if pop > 1000000:
                    score += 0.15
                elif pop > 100000:
                    score += 0.10
                elif pop > 10000:
                    score += 0.05

        # Preceded by location preposition
        prep_pattern = rf'\b(in|at|to|from|near|visit)\s+{re.escape(entity_lower)}\b'
        if re.search(prep_pattern, text_lower):
            score += 0.20

        # Followed by venue word (likely venue name, not location)
        venue_pattern = rf'\b{re.escape(entity_lower)}\s+({"|".join(self.VENUE_WORDS)})\b'
        if re.search(venue_pattern, text_lower):
            score -= 0.35  # Increased penalty

        # Check for "[demonym] [venue]" pattern like "French cafe", "Thai restaurant"
        for venue in self.VENUE_WORDS:
            if venue in text_lower:
                # If entity appears right before a venue word, heavily penalize
                pattern = rf'\b{re.escape(entity_lower)}\s+{venue}\b'
                if re.search(pattern, text_lower):
                    score -= 0.40
                    break

        # Is a demonym (adjective form) - lower priority
        if self.country_detector.is_demonym(entity_lower):
            score -= 0.15

        # Is country name but a CITY is explicitly in GeoNames AND in text - prefer city
        if self.country_detector.is_country_name(entity['word']):
            # Check if there's a known city also mentioned in text
            for other in all_entities:
                other_lower = other['word'].lower()
                if other_lower != entity_lower:
                    if self.cities_db.exists(other['word']):
                        # There's a real city - penalize the country
                        score -= 0.25
                        break

            # Also check if a city name appears in the text but wasn't extracted
            for city_name in ['sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
                             'london', 'paris', 'tokyo', 'new york', 'chicago',
                             'bangkok', 'singapore', 'hong kong']:
                if city_name in text_lower and city_name != entity_lower:
                    score -= 0.20
                    break

        # Source penalty
        source = entity.get('source', '')
        if source == 'text_country_detect':
            score -= 0.15
        elif source == 'org_country_detect':
            score -= 0.10

        return score

    def _extract_from_doc(self, doc, text: str = '') -> List[Dict]:
        """Extract location entities from spaCy doc."""
        entities = []

        for ent in doc.ents:
            word = ent.text.strip()

            if ent.label_ in ['GPE', 'LOC']:
                if word.lower() in self.BLACKLIST or len(word) < 2:
                    continue
                entities.append({
                    'word': word,
                    'entity_type': ent.label_,
                    'confidence': 0.90 if ent.label_ == 'GPE' else 0.80,
                    'source': 'ner_direct',
                })

            elif ent.label_ in ['ORG', 'FAC']:
                # Check for embedded GPE
                org_doc = self.nlp(word)
                for org_ent in org_doc.ents:
                    if org_ent.label_ == 'GPE':
                        entities.append({
                            'word': org_ent.text.strip(),
                            'entity_type': 'GPE',
                            'confidence': 0.75,
                            'source': 'embedded_in_org',
                        })
                        break
                else:
                    detected = self.country_detector.detect_country(word)
                    if detected:
                        country_name = self.country_detector.get_country_name(detected)
                        if country_name:
                            entities.append({
                                'word': country_name,
                                'entity_type': 'GPE',
                                'confidence': 0.65,
                                'source': 'org_country_detect',
                            })

        return entities

    def _extract_countries_fallback(self, text: str) -> List[Dict]:
        """Fallback: detect countries/demonyms from text."""
        entities = []
        detected = self.country_detector.detect_country(text)
        if detected:
            country_name = self.country_detector.get_country_name(detected)
            if country_name:
                entities.append({
                    'word': country_name,
                    'entity_type': 'GPE',
                    'confidence': 0.60,
                    'source': 'text_country_detect',
                })
        return entities

    def extract(self, text: str) -> List[Dict]:
        """Extract location entities with scoring."""
        if not text or len(text.strip()) < 3:
            return []

        doc = self.nlp(text)
        entities = self._extract_from_doc(doc, text)

        # Try normalized text
        normalized = self._normalize_text(text)
        if normalized != text:
            norm_doc = self.nlp(normalized)
            norm_entities = self._extract_from_doc(norm_doc, text)
            seen = {e['word'].lower(): e for e in entities}
            for e in norm_entities:
                key = e['word'].lower()
                if key not in seen or e['confidence'] > seen[key]['confidence']:
                    seen[key] = e
            entities = list(seen.values())

        # Direct GeoNames lookup for words that might be cities
        # This catches cases where NER misses known places
        text_lower = text.lower()
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)  # Capitalized words
        words += re.findall(r'\b[a-z]{4,}\b', text_lower)  # Lowercase words 4+ chars

        seen_entities = {e['word'].lower() for e in entities}
        for word in words:
            word_clean = word.strip()
            if word_clean.lower() in seen_entities:
                continue
            if word_clean.lower() in self.BLACKLIST:
                continue
            if self.cities_db.exists(word_clean):
                city_info = self.cities_db.lookup(word_clean)
                if city_info and city_info.get('population', 0) > 50000:
                    entities.append({
                        'word': city_info['name'],
                        'entity_type': 'GPE',
                        'confidence': 0.85,
                        'source': 'geonames_direct',
                    })
                    seen_entities.add(word_clean.lower())

        # Fallback: country detection
        if not entities:
            entities = self._extract_countries_fallback(text)

        # Score all entities
        for e in entities:
            e['score'] = self._score_entity(e, text, entities)

        entities.sort(key=lambda x: -x['score'])
        return entities

    def extract_batch(self, texts: List[str], batch_size: int = 50) -> List[List[Dict]]:
        """Batch extraction."""
        results = []
        docs = list(self.nlp.pipe(texts, batch_size=batch_size))
        normalized_texts = [self._normalize_text(t) for t in texts]
        norm_docs = list(self.nlp.pipe(normalized_texts, batch_size=batch_size))

        for i, (doc, norm_doc, text, norm_text) in enumerate(zip(docs, norm_docs, texts, normalized_texts)):
            entities = self._extract_from_doc(doc, text)
            if norm_text != text:
                norm_entities = self._extract_from_doc(norm_doc, text)
                seen = {e['word'].lower(): e for e in entities}
                for e in norm_entities:
                    key = e['word'].lower()
                    if key not in seen or e['confidence'] > seen[key]['confidence']:
                        seen[key] = e
                entities = list(seen.values())

            # Direct GeoNames lookup for words that might be cities
            text_lower = text.lower()
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text)
            words += re.findall(r'\b[a-z]{4,}\b', text_lower)

            seen_entities = {e['word'].lower() for e in entities}
            for word in words:
                word_clean = word.strip()
                if word_clean.lower() in seen_entities:
                    continue
                if word_clean.lower() in self.BLACKLIST:
                    continue
                if self.cities_db.exists(word_clean):
                    city_info = self.cities_db.lookup(word_clean)
                    if city_info and city_info.get('population', 0) > 50000:
                        entities.append({
                            'word': city_info['name'],
                            'entity_type': 'GPE',
                            'confidence': 0.85,
                            'source': 'geonames_direct',
                        })
                        seen_entities.add(word_clean.lower())

            if not entities:
                entities = self._extract_countries_fallback(text)
            for e in entities:
                e['score'] = self._score_entity(e, text, entities)
            entities.sort(key=lambda x: -x['score'])
            results.append(entities)

            if (i + 1) % 1000 == 0:
                logger.info(f"NER: {i + 1}/{len(texts)}")

        return results


# =============================================================================
# SMART GEOCODER WITH POPULATION RANKING
# =============================================================================

class SmartGeocoder:
    """Geocoder using GeoNames cities database with population ranking."""

    def __init__(self, cache_file: str = 'geocode_cache.json', home_country: str = 'AU'):
        from geopy.geocoders import Nominatim, ArcGIS
        from geopy.exc import (
            GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError,
            GeocoderInsufficientPrivileges, GeocoderRateLimited
        )

        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        self.home_country = home_country.lower()

        unique_id = str(uuid.uuid4())[:8]
        self.user_agent = f'LocationExtractor/9.0_{unique_id}'

        self.nominatim = Nominatim(user_agent=self.user_agent, timeout=15)
        self.arcgis = ArcGIS(timeout=15)

        self.country_detector = CountryDetector()
        self.cities_db = GeoNamesCities()

        self._geocoder_exceptions = (
            GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError,
            GeocoderInsufficientPrivileges, GeocoderRateLimited
        )

        self._last_request_time = 0
        self._min_delay = 1.5

        logger.info(f"Geocoder ready. Cache: {len(self.cache)} entries")

    def _load_cache(self) -> Dict:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _rate_limit_wait(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()

    def _safe_geocode(self, query: str, use_arcgis: bool = False, **kwargs) -> Optional[any]:
        """Geocode with retry and fallback."""
        max_attempts = 3
        geolocator = self.arcgis if use_arcgis else self.nominatim

        for attempt in range(max_attempts):
            try:
                self._rate_limit_wait()
                result = geolocator.geocode(query, **kwargs)
                return result
            except self._geocoder_exceptions as e:
                wait_time = 5 * (2 ** attempt)
                logger.warning(f"Geocode attempt {attempt + 1} failed for '{query}': {e}")
                if attempt < max_attempts - 1:
                    time.sleep(wait_time)
                elif not use_arcgis:
                    return self._safe_geocode(query, use_arcgis=True, **kwargs)
            except Exception as e:
                logger.error(f"Unexpected error for '{query}': {e}")
                break
        return None

    def geocode(self, entity: str, context: str = None, entity_info: Dict = None) -> Optional[Dict]:
        """
        Geocode with GeoNames cities database + fallback to Nominatim.

        Uses population-based ranking for disambiguation.
        """
        if not entity or len(entity.strip()) < 2:
            return None

        entity = entity.strip()
        cache_key = f"{entity.lower()}|{context[:50] if context else ''}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Step 1: Check GeoNames cities database first
        country_hint = None
        if context:
            country_hint = self.country_detector.detect_country(context)
            au_state = self.country_detector.detect_au_state(context)
            if au_state:
                country_hint = 'au'

        # Check if entity is in our curated cities database
        city_info = self.cities_db.lookup(entity, country_hint)

        if city_info:
            # Found in GeoNames - use this data directly
            geo_result = {
                'lat': city_info['lat'],
                'lon': city_info['lon'],
                'country': '',  # Will be filled by country code
                'country_code': city_info['country_code'],
                'state': city_info['admin1'],
                'city': city_info['name'],
                'type': city_info['feature_code'],
                'display_name': f"{city_info['name']}, {city_info['admin1']}, {city_info['country_code']}",
                'search_query': entity,
                'source': 'geonames_cities',
                'population': city_info['population']
            }
            self.cache[cache_key] = geo_result
            return geo_result

        # Step 2: If entity is a country, return country centroid
        if self.country_detector.is_country_name(entity):
            country_code = self.country_detector.detect_country(entity)
            if country_code:
                # Use Nominatim for country centroid
                result = self._safe_geocode(entity, exactly_one=True, addressdetails=True, language='en')
                if result:
                    address = result.raw.get('address', {})
                    geo_result = {
                        'lat': result.latitude,
                        'lon': result.longitude,
                        'country': address.get('country', entity),
                        'country_code': country_code.upper(),
                        'state': '',
                        'city': '',
                        'type': 'country',
                        'display_name': result.raw.get('display_name', ''),
                        'search_query': entity,
                        'source': 'nominatim_country'
                    }
                    self.cache[cache_key] = geo_result
                    return geo_result

        # Step 3: Fallback to Nominatim with country hints
        try:
            search_query = entity

            if country_hint and country_hint != self.home_country:
                country_name = self.country_detector.get_country_name(country_hint)
                if country_name:
                    search_query = f"{entity}, {country_name}"
                    result = self._safe_geocode(search_query, exactly_one=True,
                                               addressdetails=True, language='en')
            else:
                # Try home country first for non-famous places
                result = self._safe_geocode(entity, exactly_one=True,
                                           country_codes=[self.home_country],
                                           addressdetails=True, language='en')

            # Global fallback
            if not result:
                result = self._safe_geocode(search_query, exactly_one=True,
                                           addressdetails=True, language='en')

            if result:
                address = result.raw.get('address', {})
                geo_result = {
                    'lat': result.latitude,
                    'lon': result.longitude,
                    'country': address.get('country', ''),
                    'country_code': address.get('country_code', '').upper(),
                    'state': address.get('state', address.get('region', '')),
                    'city': address.get('city', address.get('town',
                            address.get('village', address.get('suburb', '')))),
                    'type': result.raw.get('type', ''),
                    'display_name': result.raw.get('display_name', ''),
                    'search_query': search_query,
                    'source': 'nominatim'
                }
                self.cache[cache_key] = geo_result
                return geo_result

            self.cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"Geocoding failed for '{entity}': {e}")
            self.cache[cache_key] = None
            return None

    def geocode_batch(self, entities: List[str], contexts: List[str] = None,
                      entity_infos: List[Dict] = None):
        """Batch geocode."""
        if contexts is None:
            contexts = [''] * len(entities)
        if entity_infos is None:
            entity_infos = [None] * len(entities)

        to_geocode = []
        for e, c, info in zip(entities, contexts, entity_infos):
            if e:
                cache_key = f"{e.lower().strip()}|{c[:50] if c else ''}"
                if cache_key not in self.cache:
                    to_geocode.append((e, c, info))

        seen = set()
        unique = []
        for item in to_geocode:
            key = (item[0].lower(), item[1][:50] if item[1] else '')
            if key not in seen:
                seen.add(key)
                unique.append(item)

        logger.info(f"Geocoding: {len(unique)} new queries")

        for i, (entity, context, info) in enumerate(unique):
            self.geocode(entity, context, entity_info=info)
            if (i + 1) % 5 == 0:
                logger.info(f"Geocoding: {i + 1}/{len(unique)}")
                self.save_cache()

        self.save_cache()


# =============================================================================
# FEATURE CALCULATOR
# =============================================================================

class FeatureCalculator:
    """Calculate ML features from geocoded results."""

    def __init__(self, reference_lat: float, reference_lon: float, home_country: str = 'AU'):
        self.ref_lat = reference_lat
        self.ref_lon = reference_lon
        self.home_country = home_country.upper()

    def haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def calculate(self, geo_result: Optional[Dict], ner_score: float = 0.0) -> Dict:
        features = {
            'has_location': 0, 'lat': 0.0, 'lon': 0.0,
            'distance_km': 0.0, 'travel_hours': 0.0,
            'is_international': 0, 'is_domestic': 0,
            'ner_score': round(ner_score, 3),
            'country': '', 'country_code': '', 'state': '', 'city': '',
            'location_name': ''
        }

        if not geo_result:
            return features

        lat, lon = geo_result.get('lat', 0), geo_result.get('lon', 0)
        country_code = geo_result.get('country_code', '').upper()

        if lat == 0 and lon == 0:
            return features

        features['has_location'] = 1
        features['lat'] = round(lat, 4)
        features['lon'] = round(lon, 4)
        features['country'] = geo_result.get('country', '')
        features['country_code'] = country_code
        features['state'] = geo_result.get('state', '')
        features['city'] = geo_result.get('city', '')
        features['location_name'] = geo_result.get('display_name', '')[:100]

        distance = self.haversine(self.ref_lat, self.ref_lon, lat, lon)
        features['distance_km'] = round(distance, 1)

        if country_code != self.home_country or distance > 1000:
            features['travel_hours'] = round((distance / 800) + 2, 1)
        elif distance > 300:
            features['travel_hours'] = round(min((distance / 800) + 2, distance / 80), 1)
        else:
            features['travel_hours'] = round(distance / 80, 1) if distance > 0 else 0

        features['is_international'] = 1 if country_code != self.home_country else 0
        features['is_domestic'] = 1 if country_code == self.home_country else 0

        return features


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class LocationPipeline:
    """
    Location extraction pipeline v9 - Research-backed best practices.

    Key features:
    1. GeoNames cities15000 database with population data
    2. Population-based ranking for disambiguation
    3. Feature code hierarchy (PPLC > PPLA > PPL)
    4. Contextual NER scoring
    5. Demonym/country detection via pycountry
    """

    def __init__(
            self,
            reference_lat: float,
            reference_lon: float,
            home_country: str = 'AU',
            cache_file: str = 'geocode_cache_v9.json'
    ):
        logger.info("Initializing LocationPipeline V9 (GeoNames + Population Ranking)...")

        self.ner = SpacyNER()
        self.geocoder = SmartGeocoder(cache_file=cache_file, home_country=home_country)
        self.feature_calc = FeatureCalculator(reference_lat, reference_lon, home_country)

        logger.info("LocationPipeline V9 ready")

    def combine_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.Series:
        combined = pd.Series([''] * len(df), index=df.index)
        for col in columns:
            if col in df.columns:
                combined = combined + ' ' + df[col].fillna('').astype(str)
        return combined.str.strip()

    def process_dataframe(
            self,
            df: pd.DataFrame,
            text_columns: List[str],
            output_prefix: str = 'loc_'
    ) -> pd.DataFrame:
        df = df.copy()
        n_rows = len(df)

        logger.info(f"Processing {n_rows} rows...")
        combined = self.combine_columns(df, text_columns)

        # NER extraction
        logger.info("Running NER...")
        all_entities = self.ner.extract_batch(combined.tolist())

        # Select best entity
        best_entities = []
        for entities in all_entities:
            if entities:
                best_entities.append(entities[0])  # Already sorted by score
            else:
                best_entities.append(None)

        # Geocoding
        entities_list = [e['word'] if e else '' for e in best_entities]
        contexts = combined.tolist()
        self.geocoder.geocode_batch(entities_list, contexts, best_entities)

        # Feature calculation
        logger.info("Calculating features...")
        all_features = []

        for i, best in enumerate(best_entities):
            if best:
                cache_key = f"{best['word'].lower().strip()}|{contexts[i][:50] if contexts[i] else ''}"
                geo = self.geocoder.cache.get(cache_key)
                features = self.feature_calc.calculate(geo, best.get('score', 0))
                features['extracted_entity'] = best['word']
            else:
                features = self.feature_calc.calculate(None)
                features['extracted_entity'] = ''

            all_features.append(features)

        # Add to DataFrame
        features_df = pd.DataFrame(all_features)
        for col in features_df.columns:
            df[f'{output_prefix}{col}'] = features_df[col].values

        has_loc = df[f'{output_prefix}has_location'].sum()
        logger.info(f"Complete: {has_loc}/{n_rows} ({100 * has_loc / n_rows:.1f}%) have location")

        return df


# =============================================================================
# DEMO
# =============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("LOCATION EXTRACTOR V9 - GeoNames + Population Ranking")
    print("=" * 80)

    sample_data = pd.DataFrame({
        'PURPOSE': [
            'Client dinner at Crown Sydney with 5 partners',
            'Team meeting in Melbourne CBD',
            'Flight to Brisbane for conference',
            'Dinner at thai restaurant',
            'Meeting at srilankan hotel',
            'Trip to phillipines for audit',
            'Client dinner at Noma Copenhagen',
            'Business dinner Gaggan Bangkok',
            'Meeting over dinner at Alinea Chicago',
            'VIP dinner Masa New York',
            'Dinner at The French Cafe',
            'Meeting at China Club',
            'Lunch at China Doll Sydney',
            'Stay at The Savoy London',
            'Stay at Bellagio Las Vegas',
            'Meeting near Eiffel Tower Paris',
            'Meeting at Amazon HQ Seattle',
            'Visit to Apple Park Cupertino',
            'Client meeting Antananarivo',
            'Mine visit Potosí Bolivia',
            'Christmas party Gampola and kandy Sri Lanka',
        ],
        'CHARGE_DESCRIPTION': [
            'CROWN SYDNEY', 'THE GEORGE ON COLLINS', 'QANTAS AIRWAYS',
            'THAI PALACE RESTAURANT', 'COLOMBO GRAND HOTEL', 'MANILA HOTEL',
            'NOMA RESTAURANT', 'GAGGAN ANAND', 'ALINEA', 'MASA NYC',
            'THE FRENCH CAFE', 'CHINA CLUB SYDNEY', 'CHINA DOLL',
            'THE SAVOY', 'BELLAGIO LAS VEGAS', 'EIFFEL TOWER DINING',
            'AMAZON.COM INC', 'APPLE INC', 'CARLTON ANTANANARIVO',
            'POTOSI MINING CORP', 'SRI LANKA CATERING',
        ]
    })

    pipeline = LocationPipeline(
        reference_lat=-33.8688,
        reference_lon=151.2093,
        home_country='AU'
    )

    result_df = pipeline.process_dataframe(
        sample_data,
        text_columns=['PURPOSE', 'CHARGE_DESCRIPTION']
    )

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    cols = ['PURPOSE', 'loc_extracted_entity', 'loc_has_location', 'loc_city',
            'loc_country_code', 'loc_distance_km', 'loc_is_international', 'loc_ner_score']

    pd.set_option('display.max_colwidth', 50)
    pd.set_option('display.width', None)
    print(result_df[[c for c in cols if c in result_df.columns]].to_string())

    pipeline.geocoder.save_cache()