"""
Australian Locations database and state mapping for FBT pipeline.
Extracted from notebook to enable reuse across modules.
"""
from typing import Dict, Set

AUSTRALIAN_LOCATIONS: Dict[str, Dict[str, object]] = {
    # Major Cities
    'sydney': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'city'},
    'melbourne': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'city'},
    'brisbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'city'},
    'perth': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'city'},
    'adelaide': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'city'},
    'hobart': {'lat': -42.8821, 'lon': 147.3272, 'state': 'TAS', 'type': 'city'},
    'darwin': {'lat': -12.4634, 'lon': 130.8456, 'state': 'NT', 'type': 'city'},
    'canberra': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'city'},
    
    # Regional NSW
    'newcastle': {'lat': -32.9283, 'lon': 151.7817, 'state': 'NSW', 'type': 'regional'},
    'wollongong': {'lat': -34.4278, 'lon': 150.8931, 'state': 'NSW', 'type': 'regional'},
    'dubbo': {'lat': -32.2569, 'lon': 148.6011, 'state': 'NSW', 'type': 'regional'},
    'tamworth': {'lat': -31.0830, 'lon': 150.9170, 'state': 'NSW', 'type': 'regional'},
    'wagga wagga': {'lat': -35.1082, 'lon': 147.3598, 'state': 'NSW', 'type': 'regional'},
    'wagga': {'lat': -35.1082, 'lon': 147.3598, 'state': 'NSW', 'type': 'regional'},
    'orange': {'lat': -33.2840, 'lon': 149.1004, 'state': 'NSW', 'type': 'regional'},
    'bathurst': {'lat': -33.4190, 'lon': 149.5778, 'state': 'NSW', 'type': 'regional'},
    'albury': {'lat': -36.0737, 'lon': 146.9135, 'state': 'NSW', 'type': 'regional'},
    'broken hill': {'lat': -31.9539, 'lon': 141.4428, 'state': 'NSW', 'type': 'regional'},
    'armidale': {'lat': -30.5150, 'lon': 151.6500, 'state': 'NSW', 'type': 'regional'},
    'lismore': {'lat': -28.8120, 'lon': 153.2790, 'state': 'NSW', 'type': 'regional'},
    'grafton': {'lat': -29.6850, 'lon': 152.9330, 'state': 'NSW', 'type': 'regional'},
    'coffs harbour': {'lat': -30.2963, 'lon': 153.1135, 'state': 'NSW', 'type': 'regional'},
    'port macquarie': {'lat': -31.4333, 'lon': 152.9000, 'state': 'NSW', 'type': 'regional'},
    'moree': {'lat': -29.4640, 'lon': 149.8470, 'state': 'NSW', 'type': 'regional'},
    'goulburn': {'lat': -34.7547, 'lon': 149.7186, 'state': 'NSW', 'type': 'regional'},
    'nowra': {'lat': -34.8800, 'lon': 150.6000, 'state': 'NSW', 'type': 'regional'},
    'griffith': {'lat': -34.2890, 'lon': 146.0400, 'state': 'NSW', 'type': 'regional'},
    'parkes': {'lat': -33.1370, 'lon': 148.1750, 'state': 'NSW', 'type': 'regional'},
    'forbes': {'lat': -33.3850, 'lon': 148.0170, 'state': 'NSW', 'type': 'regional'},
    'cowra': {'lat': -33.8330, 'lon': 148.6830, 'state': 'NSW', 'type': 'regional'},
    'young': {'lat': -34.3130, 'lon': 148.3000, 'state': 'NSW', 'type': 'regional'},
    'mudgee': {'lat': -32.6000, 'lon': 149.5830, 'state': 'NSW', 'type': 'regional'},
    'cobar': {'lat': -31.4950, 'lon': 145.8380, 'state': 'NSW', 'type': 'regional'},
    'bourke': {'lat': -30.0900, 'lon': 145.9380, 'state': 'NSW', 'type': 'regional'},
    'walgett': {'lat': -30.0200, 'lon': 148.1170, 'state': 'NSW', 'type': 'regional'},
    'narrabri': {'lat': -30.3250, 'lon': 149.7830, 'state': 'NSW', 'type': 'regional'},
    'gunnedah': {'lat': -30.9800, 'lon': 150.2500, 'state': 'NSW', 'type': 'regional'},
    'inverell': {'lat': -29.7750, 'lon': 151.1170, 'state': 'NSW', 'type': 'regional'},
    'glen innes': {'lat': -29.7330, 'lon': 151.7330, 'state': 'NSW', 'type': 'regional'},
    'tenterfield': {'lat': -29.0500, 'lon': 152.0170, 'state': 'NSW', 'type': 'regional'},
    
    # Regional QLD
    'gold coast': {'lat': -28.0167, 'lon': 153.4000, 'state': 'QLD', 'type': 'regional'},
    'sunshine coast': {'lat': -26.6500, 'lon': 153.0667, 'state': 'QLD', 'type': 'regional'},
    'cairns': {'lat': -16.9186, 'lon': 145.7781, 'state': 'QLD', 'type': 'regional'},
    'townsville': {'lat': -19.2590, 'lon': 146.8169, 'state': 'QLD', 'type': 'regional'},
    'toowoomba': {'lat': -27.5598, 'lon': 151.9507, 'state': 'QLD', 'type': 'regional'},
    'rockhampton': {'lat': -23.3791, 'lon': 150.5100, 'state': 'QLD', 'type': 'regional'},
    'mackay': {'lat': -21.1411, 'lon': 149.1861, 'state': 'QLD', 'type': 'regional'},
    'bundaberg': {'lat': -24.8661, 'lon': 152.3489, 'state': 'QLD', 'type': 'regional'},
    'gladstone': {'lat': -23.8427, 'lon': 151.2555, 'state': 'QLD', 'type': 'regional'},
    'hervey bay': {'lat': -25.2900, 'lon': 152.8500, 'state': 'QLD', 'type': 'regional'},
    'roma': {'lat': -26.5700, 'lon': 148.7850, 'state': 'QLD', 'type': 'regional'},
    'charleville': {'lat': -26.4030, 'lon': 146.2430, 'state': 'QLD', 'type': 'regional'},
    'longreach': {'lat': -23.4420, 'lon': 144.2500, 'state': 'QLD', 'type': 'regional'},
    'mount isa': {'lat': -20.7256, 'lon': 139.4927, 'state': 'QLD', 'type': 'regional'},
    'cloncurry': {'lat': -20.7050, 'lon': 140.5060, 'state': 'QLD', 'type': 'regional'},
    'emerald': {'lat': -23.5270, 'lon': 148.1640, 'state': 'QLD', 'type': 'regional'},
    'dalby': {'lat': -27.1810, 'lon': 151.2650, 'state': 'QLD', 'type': 'regional'},
    'kingaroy': {'lat': -26.5400, 'lon': 151.8400, 'state': 'QLD', 'type': 'regional'},
    'warwick': {'lat': -28.2150, 'lon': 152.0350, 'state': 'QLD', 'type': 'regional'},
    'stanthorpe': {'lat': -28.6570, 'lon': 151.9350, 'state': 'QLD', 'type': 'regional'},
    'goondiwindi': {'lat': -28.5470, 'lon': 150.3100, 'state': 'QLD', 'type': 'regional'},
    'st george': {'lat': -28.0370, 'lon': 148.5830, 'state': 'QLD', 'type': 'regional'},
    'cunnamulla': {'lat': -28.0670, 'lon': 145.6830, 'state': 'QLD', 'type': 'regional'},
    'charters towers': {'lat': -20.0760, 'lon': 146.2610, 'state': 'QLD', 'type': 'regional'},
    'ayr': {'lat': -19.5740, 'lon': 147.4040, 'state': 'QLD', 'type': 'regional'},
    'ingham': {'lat': -18.6500, 'lon': 146.1670, 'state': 'QLD', 'type': 'regional'},
    'innisfail': {'lat': -17.5240, 'lon': 146.0330, 'state': 'QLD', 'type': 'regional'},
    'atherton': {'lat': -17.2670, 'lon': 145.4830, 'state': 'QLD', 'type': 'regional'},
    'mareeba': {'lat': -17.0000, 'lon': 145.4330, 'state': 'QLD', 'type': 'regional'},
    'biloela': {'lat': -24.4000, 'lon': 150.5170, 'state': 'QLD', 'type': 'regional'},
    'monto': {'lat': -24.8670, 'lon': 151.1170, 'state': 'QLD', 'type': 'regional'},
    'gayndah': {'lat': -25.6300, 'lon': 151.6170, 'state': 'QLD', 'type': 'regional'},
    'murgon': {'lat': -26.2400, 'lon': 151.9400, 'state': 'QLD', 'type': 'regional'},
    
    # Regional VIC
    'geelong': {'lat': -38.1499, 'lon': 144.3617, 'state': 'VIC', 'type': 'regional'},
    'ballarat': {'lat': -37.5622, 'lon': 143.8503, 'state': 'VIC', 'type': 'regional'},
    'bendigo': {'lat': -36.7570, 'lon': 144.2794, 'state': 'VIC', 'type': 'regional'},
    'shepparton': {'lat': -36.3833, 'lon': 145.4000, 'state': 'VIC', 'type': 'regional'},
    'mildura': {'lat': -34.2087, 'lon': 142.1311, 'state': 'VIC', 'type': 'regional'},
    'warrnambool': {'lat': -38.3818, 'lon': 142.4876, 'state': 'VIC', 'type': 'regional'},
    'wodonga': {'lat': -36.1217, 'lon': 146.8883, 'state': 'VIC', 'type': 'regional'},
    'horsham': {'lat': -36.7117, 'lon': 142.2000, 'state': 'VIC', 'type': 'regional'},
    'wangaratta': {'lat': -36.3578, 'lon': 146.3122, 'state': 'VIC', 'type': 'regional'},
    'sale': {'lat': -38.1000, 'lon': 147.0667, 'state': 'VIC', 'type': 'regional'},
    'traralgon': {'lat': -38.1950, 'lon': 146.5400, 'state': 'VIC', 'type': 'regional'},
    'bairnsdale': {'lat': -37.8230, 'lon': 147.6100, 'state': 'VIC', 'type': 'regional'},
    'echuca': {'lat': -36.1300, 'lon': 144.7500, 'state': 'VIC', 'type': 'regional'},
    'swan hill': {'lat': -35.3380, 'lon': 143.5500, 'state': 'VIC', 'type': 'regional'},
    'hamilton': {'lat': -37.7440, 'lon': 142.0220, 'state': 'VIC', 'type': 'regional'},
    'colac': {'lat': -38.3400, 'lon': 143.5900, 'state': 'VIC', 'type': 'regional'},
    'ararat': {'lat': -37.2840, 'lon': 142.9300, 'state': 'VIC', 'type': 'regional'},
    'stawell': {'lat': -37.0560, 'lon': 142.7800, 'state': 'VIC', 'type': 'regional'},
    'castlemaine': {'lat': -37.0670, 'lon': 144.2170, 'state': 'VIC', 'type': 'regional'},
    'kyneton': {'lat': -37.2500, 'lon': 144.4500, 'state': 'VIC', 'type': 'regional'},
    'seymour': {'lat': -37.0260, 'lon': 145.1390, 'state': 'VIC', 'type': 'regional'},
    'benalla': {'lat': -36.5520, 'lon': 145.9830, 'state': 'VIC', 'type': 'regional'},
    'cobram': {'lat': -35.9200, 'lon': 145.6500, 'state': 'VIC', 'type': 'regional'},
    'yarrawonga': {'lat': -36.0300, 'lon': 146.0000, 'state': 'VIC', 'type': 'regional'},
    'kyabram': {'lat': -36.3170, 'lon': 145.0500, 'state': 'VIC', 'type': 'regional'},
    'rochester': {'lat': -36.3670, 'lon': 144.7000, 'state': 'VIC', 'type': 'regional'},
    'kerang': {'lat': -35.7330, 'lon': 143.9170, 'state': 'VIC', 'type': 'regional'},
    
    # Regional SA
    'mount gambier': {'lat': -37.8297, 'lon': 140.7811, 'state': 'SA', 'type': 'regional'},
    'whyalla': {'lat': -33.0333, 'lon': 137.5167, 'state': 'SA', 'type': 'regional'},
    'port lincoln': {'lat': -34.7333, 'lon': 135.8500, 'state': 'SA', 'type': 'regional'},
    'port augusta': {'lat': -32.4936, 'lon': 137.7825, 'state': 'SA', 'type': 'regional'},
    'port pirie': {'lat': -33.1858, 'lon': 138.0169, 'state': 'SA', 'type': 'regional'},
    'murray bridge': {'lat': -35.1197, 'lon': 139.2756, 'state': 'SA', 'type': 'regional'},
    'renmark': {'lat': -34.1760, 'lon': 140.7470, 'state': 'SA', 'type': 'regional'},
    'berri': {'lat': -34.2830, 'lon': 140.6000, 'state': 'SA', 'type': 'regional'},
    'loxton': {'lat': -34.4500, 'lon': 140.5670, 'state': 'SA', 'type': 'regional'},
    'kadina': {'lat': -33.9670, 'lon': 137.7170, 'state': 'SA', 'type': 'regional'},
    'clare': {'lat': -33.8330, 'lon': 138.6000, 'state': 'SA', 'type': 'regional'},
    'tanunda': {'lat': -34.5230, 'lon': 138.9600, 'state': 'SA', 'type': 'regional'},
    'nuriootpa': {'lat': -34.4670, 'lon': 139.0000, 'state': 'SA', 'type': 'regional'},
    'naracoorte': {'lat': -36.9500, 'lon': 140.7330, 'state': 'SA', 'type': 'regional'},
    'bordertown': {'lat': -36.3100, 'lon': 140.7700, 'state': 'SA', 'type': 'regional'},
    
    # Regional WA
    'bunbury': {'lat': -33.3261, 'lon': 115.6394, 'state': 'WA', 'type': 'regional'},
    'geraldton': {'lat': -28.7775, 'lon': 114.6147, 'state': 'WA', 'type': 'regional'},
    'kalgoorlie': {'lat': -30.7489, 'lon': 121.4658, 'state': 'WA', 'type': 'regional'},
    'albany': {'lat': -35.0275, 'lon': 117.8839, 'state': 'WA', 'type': 'regional'},
    'mandurah': {'lat': -32.5269, 'lon': 115.7217, 'state': 'WA', 'type': 'regional'},
    'broome': {'lat': -17.9614, 'lon': 122.2359, 'state': 'WA', 'type': 'regional'},
    'karratha': {'lat': -20.7361, 'lon': 116.8467, 'state': 'WA', 'type': 'regional'},
    'port hedland': {'lat': -20.3108, 'lon': 118.5753, 'state': 'WA', 'type': 'regional'},
    'esperance': {'lat': -33.8611, 'lon': 121.8919, 'state': 'WA', 'type': 'regional'},
    'carnarvon': {'lat': -24.8840, 'lon': 113.6590, 'state': 'WA', 'type': 'regional'},
    'kununurra': {'lat': -15.7730, 'lon': 128.7380, 'state': 'WA', 'type': 'regional'},
    'collie': {'lat': -33.3600, 'lon': 116.1500, 'state': 'WA', 'type': 'regional'},
    'katanning': {'lat': -33.6900, 'lon': 117.5500, 'state': 'WA', 'type': 'regional'},
    'narrogin': {'lat': -32.9330, 'lon': 117.1830, 'state': 'WA', 'type': 'regional'},
    'merredin': {'lat': -31.4830, 'lon': 118.2830, 'state': 'WA', 'type': 'regional'},
    'northam': {'lat': -31.6500, 'lon': 116.6670, 'state': 'WA', 'type': 'regional'},
    'moora': {'lat': -30.6400, 'lon': 116.0170, 'state': 'WA', 'type': 'regional'},
    'dalwallinu': {'lat': -30.2770, 'lon': 116.6630, 'state': 'WA', 'type': 'regional'},
    
    # Regional NT
    'alice springs': {'lat': -23.6980, 'lon': 133.8807, 'state': 'NT', 'type': 'regional'},
    'katherine': {'lat': -14.4650, 'lon': 132.2635, 'state': 'NT', 'type': 'regional'},
    'tennant creek': {'lat': -19.6497, 'lon': 134.1917, 'state': 'NT', 'type': 'regional'},
    
    # Regional TAS
    'launceston': {'lat': -41.4332, 'lon': 147.1441, 'state': 'TAS', 'type': 'regional'},
    'devonport': {'lat': -41.1760, 'lon': 146.3510, 'state': 'TAS', 'type': 'regional'},
    'burnie': {'lat': -41.0556, 'lon': 145.9056, 'state': 'TAS', 'type': 'regional'},
    
    # Airports (IATA codes)
    'syd': {'lat': -33.9399, 'lon': 151.1753, 'state': 'NSW', 'type': 'airport'},
    'mel': {'lat': -37.6690, 'lon': 144.8410, 'state': 'VIC', 'type': 'airport'},
    'bne': {'lat': -27.3942, 'lon': 153.1218, 'state': 'QLD', 'type': 'airport'},
    'per': {'lat': -31.9403, 'lon': 115.9670, 'state': 'WA', 'type': 'airport'},
    'adl': {'lat': -34.9450, 'lon': 138.5306, 'state': 'SA', 'type': 'airport'},
    'cbr': {'lat': -35.3069, 'lon': 149.1950, 'state': 'ACT', 'type': 'airport'},
    'ool': {'lat': -28.1644, 'lon': 153.5047, 'state': 'QLD', 'type': 'airport'},  # Gold Coast
    'cns': {'lat': -16.8858, 'lon': 145.7553, 'state': 'QLD', 'type': 'airport'},  # Cairns
    'tsv': {'lat': -19.2525, 'lon': 146.7656, 'state': 'QLD', 'type': 'airport'},  # Townsville
    'dbo': {'lat': -32.2167, 'lon': 148.5747, 'state': 'NSW', 'type': 'airport'},  # Dubbo
    'ntl': {'lat': -32.7950, 'lon': 151.8342, 'state': 'NSW', 'type': 'airport'},  # Newcastle
    'rce': {'lat': -23.3819, 'lon': 150.4753, 'state': 'QLD', 'type': 'airport'},  # Rockhampton
    'mky': {'lat': -21.1717, 'lon': 149.1797, 'state': 'QLD', 'type': 'airport'},  # Mackay
    'isa': {'lat': -20.6639, 'lon': 139.4886, 'state': 'QLD', 'type': 'airport'},  # Mount Isa
    'eme': {'lat': -23.5675, 'lon': 148.1792, 'state': 'QLD', 'type': 'airport'},  # Emerald
    'lre': {'lat': -23.4342, 'lon': 144.2797, 'state': 'QLD', 'type': 'airport'},  # Longreach
    
    # International destinations (common business travel)
    'utrecht': {'lat': 52.0907, 'lon': 5.1214, 'state': 'NL', 'type': 'international'},
    'amsterdam': {'lat': 52.3676, 'lon': 4.9041, 'state': 'NL', 'type': 'international'},
    'netherlands': {'lat': 52.1326, 'lon': 5.2913, 'state': 'NL', 'type': 'international'},
    'singapore': {'lat': 1.3521, 'lon': 103.8198, 'state': 'SG', 'type': 'international'},
    'hong kong': {'lat': 22.3193, 'lon': 114.1694, 'state': 'HK', 'type': 'international'},
    'new zealand': {'lat': -40.9006, 'lon': 174.8860, 'state': 'NZ', 'type': 'international'},
    'auckland': {'lat': -36.8509, 'lon': 174.7645, 'state': 'NZ', 'type': 'international'},
    'wellington': {'lat': -41.2924, 'lon': 174.7787, 'state': 'NZ', 'type': 'international'},
    'london': {'lat': 51.5074, 'lon': -0.1278, 'state': 'UK', 'type': 'international'},
    'boston': {'lat': 42.3601, 'lon': -71.0589, 'state': 'US', 'type': 'international'},
    'new york': {'lat': 40.7128, 'lon': -74.0060, 'state': 'US', 'type': 'international'},
    'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'state': 'JP', 'type': 'international'},
    'beijing': {'lat': 39.9042, 'lon': 116.4074, 'state': 'CN', 'type': 'international'},
    'shanghai': {'lat': 31.2304, 'lon': 121.4737, 'state': 'CN', 'type': 'international'},
    'jakarta': {'lat': -6.2088, 'lon': 106.8456, 'state': 'ID', 'type': 'international'},
    'manila': {'lat': 14.5995, 'lon': 120.9842, 'state': 'PH', 'type': 'international'},
    'bangkok': {'lat': 13.7563, 'lon': 100.5018, 'state': 'TH', 'type': 'international'},
    'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'state': 'IN', 'type': 'international'},
    'dubai': {'lat': 25.2048, 'lon': 55.2708, 'state': 'AE', 'type': 'international'},
    
    # Australian Restaurants & Venues (Popular chains)
    'quay': {'lat': -33.8572, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'rockpool': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'aria restaurant': {'lat': -33.8584, 'lon': 151.2119, 'state': 'NSW', 'type': 'restaurant'},
    'tetsuya': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'mr wong': {'lat': -33.8704, 'lon': 151.2073, 'state': 'NSW', 'type': 'restaurant'},
    'sepia': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'est': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'bel and brio': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'golden century': {'lat': -33.8729, 'lon': 151.2065, 'state': 'NSW', 'type': 'restaurant'},
    'hubert': {'lat': -33.8680, 'lon': 151.2110, 'state': 'NSW', 'type': 'restaurant'},
    'firedoor': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'ester': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'otto': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'attica': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'brae': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'donovan': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'stokehouse': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'vue de monde': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'grossi florentino': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'milon': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'tivoli': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'restaurant'},
    'urbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'restaurant'},
    
    # Coffee Chains
    'coffee culture': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'cafe'},
    'little collins': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'cafe'},
    'brew': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'cafe'},
    'campos': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'cafe'},
    'single origin': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'cafe'},
    'two hands': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'cafe'},
    
    # Hotels & Accommodation
    'park hyatt': {'lat': -33.8572, 'lon': 151.2119, 'state': 'NSW', 'type': 'hotel'},
    'shangri-la': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'hotel'},
    'four seasons': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'hotel'},
    'langham': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'hotel'},
    'crown': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'hotel'},
    'hilton': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'hotel'},
    'westin': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'hotel'},
    'marriott': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'hotel'},
    'ritz carlton': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'hotel'},
    
    # Pubs & Bars
    'the royal': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'arbitrage': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'bar americano': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'venue'},
    'basement discotheque': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'venue'},
    
    # Fast Casual
    'greca': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'lilia': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'papi chulo': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'freddy smalls': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'barangaroo reserve': {'lat': -33.8572, 'lon': 151.2119, 'state': 'NSW', 'type': 'venue'},
    
    # Libraries
    'state library of nsw': {'lat': -33.8667, 'lon': 151.2094, 'state': 'NSW', 'type': 'library'},
    'state library of victoria': {'lat': -37.8099, 'lon': 144.9654, 'state': 'VIC', 'type': 'library'},
    'state library of queensland': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'library'},
    'state library of south australia': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'library'},
    'state library of western australia': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'library'},
    'national library of australia': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'library'},
    
    # Museums
    'australian museum': {'lat': -33.8772, 'lon': 151.2099, 'state': 'NSW', 'type': 'museum'},
    'national gallery of victoria': {'lat': -37.8226, 'lon': 144.9689, 'state': 'VIC', 'type': 'museum'},
    'queensland museum': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'museum'},
    'south australian museum': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'museum'},
    'western australian museum': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'museum'},
    'tasmanian museum and art gallery': {'lat': -42.8821, 'lon': 147.3272, 'state': 'TAS', 'type': 'museum'},
    'museum and art gallery of the northern territory': {'lat': -12.4634, 'lon': 130.8456, 'state': 'NT', 'type': 'museum'},
    'national museum of australia': {'lat': -35.2923, 'lon': 149.1217, 'state': 'ACT', 'type': 'museum'},
    
    # Tourist Attractions
    'sydney opera house': {'lat': -33.8568, 'lon': 151.2153, 'state': 'NSW', 'type': 'attraction'},
    'sydney harbour bridge': {'lat': -33.8523, 'lon': 151.2108, 'state': 'NSW', 'type': 'attraction'},
    'great barrier reef': {'lat': -18.2871, 'lon': 147.6992, 'state': 'QLD', 'type': 'attraction'},
    'uluru': {'lat': -25.3444, 'lon': 131.0369, 'state': 'NT', 'type': 'attraction'},
    'ayers rock': {'lat': -25.3444, 'lon': 131.0369, 'state': 'NT', 'type': 'attraction'},
    'bondi beach': {'lat': -33.8915, 'lon': 151.2767, 'state': 'NSW', 'type': 'attraction'},
    'great ocean road': {'lat': -38.6623, 'lon': 143.1048, 'state': 'VIC', 'type': 'attraction'},
    'daintree rainforest': {'lat': -16.1733, 'lon': 145.4187, 'state': 'QLD', 'type': 'attraction'},
    'kakadu national park': {'lat': -13.0923, 'lon': 132.3937, 'state': 'NT', 'type': 'attraction'},
    'blue mountains': {'lat': -33.7125, 'lon': 150.3117, 'state': 'NSW', 'type': 'attraction'},
    'fraser island': {'lat': -25.3333, 'lon': 153.0833, 'state': 'QLD', 'type': 'attraction'},
    'whitsunday islands': {'lat': -20.2763, 'lon': 148.7137, 'state': 'QLD', 'type': 'attraction'},
    'pinnacles': {'lat': -25.5705, 'lon': 113.7790, 'state': 'WA', 'type': 'attraction'},
    'kangaroo island': {'lat': -35.8000, 'lon': 137.2333, 'state': 'SA', 'type': 'attraction'},
    'tasmanian wilderness': {'lat': -43.0000, 'lon': 146.5000, 'state': 'TAS', 'type': 'attraction'},
    
    # Fast Food Chain Locations - Multiple outlets per city
    # McDonald's locations
    'mcdonalds sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'mcdonalds sydney north': {'lat': -33.8288, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'mcdonalds sydney south': {'lat': -33.9088, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'mcdonalds melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'mcdonalds melbourne south': {'lat': -37.8536, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'mcdonalds brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'mcdonalds brisbane north': {'lat': -27.4298, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'mcdonalds perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    'mcdonalds adelaide cbd': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'fast_food'},
    'mcdonalds canberra cbd': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'fast_food'},
    
    # Hungry Jacks locations
    'hungry jacks sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'hungry jacks sydney west': {'lat': -33.8688, 'lon': 151.1693, 'state': 'NSW', 'type': 'fast_food'},
    'hungry jacks melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'hungry jacks melbourne east': {'lat': -37.8136, 'lon': 145.0031, 'state': 'VIC', 'type': 'fast_food'},
    'hungry jacks brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'hungry jacks perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    'hungry jacks adelaide cbd': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'fast_food'},
    'hungry jacks canberra cbd': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'fast_food'},
    
    # KFC locations
    'kfc sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'kfc sydney east': {'lat': -33.8688, 'lon': 151.2493, 'state': 'NSW', 'type': 'fast_food'},
    'kfc sydney west': {'lat': -33.8688, 'lon': 151.1693, 'state': 'NSW', 'type': 'fast_food'},
    'kfc melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'kfc melbourne north': {'lat': -37.7736, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'kfc brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'kfc brisbane south': {'lat': -27.5098, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'kfc perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    'kfc adelaide cbd': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'fast_food'},
    'kfc canberra cbd': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'fast_food'},
    
    # Subway locations
    'subway sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'subway sydney north': {'lat': -33.8288, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'subway melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'subway brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'subway perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    'subway adelaide cbd': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'fast_food'},
    'subway canberra cbd': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'fast_food'},
    
    # Domino's Pizza locations
    'dominos sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'dominos sydney south': {'lat': -33.9088, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'dominos melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'dominos brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'dominos perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    'dominos adelaide cbd': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'fast_food'},
    'dominos canberra cbd': {'lat': -35.2809, 'lon': 149.1300, 'state': 'ACT', 'type': 'fast_food'},
    
    # Pizza Hut locations
    'pizza hut sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'pizza hut melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'pizza hut brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'pizza hut perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    'pizza hut adelaide cbd': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'fast_food'},
    
    # Nando's locations
    'nandos sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'nandos melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'nandos brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'nandos perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    
    # Red Rooster locations
    'red rooster sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'red rooster sydney west': {'lat': -33.8688, 'lon': 151.1693, 'state': 'NSW', 'type': 'fast_food'},
    'red rooster melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'red rooster brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'red rooster perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'fast_food'},
    
    # Chicken Treat locations
    'chicken treat sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'chicken treat melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'chicken treat brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    
    # Taco Bell locations
    'taco bell sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'taco bell melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'taco bell brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    
    # Australian Slang Terms for Locations
    # Fast Food Slang
    'macca\'s': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'maccas': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'macca\'s sydney': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'maccas sydney': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'macca\'s melbourne': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'maccas melbourne': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'fast_food'},
    'macca\'s brisbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'maccas brisbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'fast_food'},
    'hungry jack\'s': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'hungry jacks': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    
    # Other Australian Venue Slang
    'servo': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'bottle-o': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'botto': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'milk bar': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'rsl': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'rsl club': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'leagues club': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'bowling club': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'golf club': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    'sports club': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'venue'},
    
    # Regional/Location Slang
    'the bush': {'lat': -32.2569, 'lon': 148.6011, 'state': 'NSW', 'type': 'regional'},
    'outback': {'lat': -25.0000, 'lon': 135.0000, 'state': 'NT', 'type': 'regional'},
    'beachie': {'lat': -33.8915, 'lon': 151.2767, 'state': 'NSW', 'type': 'attraction'},
    'the beach': {'lat': -33.8915, 'lon': 151.2767, 'state': 'NSW', 'type': 'attraction'},
    
    # Australian Retail & Supermarket Chains
    # Grill'd locations (burger chain)
    'grill\'d': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'grill\'d sydney cbd': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'restaurant'},
    'grill\'d melbourne cbd': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'restaurant'},
    'grill\'d brisbane cbd': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'restaurant'},
    'grill\'d perth cbd': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'restaurant'},
    
    # Target locations (department store)
    'target': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'target sydney': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'target melbourne': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'retail'},
    'target brisbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'retail'},
    'target perth': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'retail'},
    'target adelaide': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'retail'},
    
    # Woolworths locations (supermarket)
    'woolworths': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'supermarket'},
    'woolworth\'s': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'supermarket'},
    'woolies': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'supermarket'},
    'woolworths sydney': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'supermarket'},
    'woolworths melbourne': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'supermarket'},
    'woolworths brisbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'supermarket'},
    'woolworths perth': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'supermarket'},
    'woolworths adelaide': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'supermarket'},
    
    # Coles locations (supermarket)
    'coles': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'supermarket'},
    'coles sydney': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'supermarket'},
    'coles melbourne': {'lat': -37.8136, 'lon': 144.9631, 'state': 'VIC', 'type': 'supermarket'},
    'coles brisbane': {'lat': -27.4698, 'lon': 153.0251, 'state': 'QLD', 'type': 'supermarket'},
    'coles perth': {'lat': -31.9505, 'lon': 115.8605, 'state': 'WA', 'type': 'supermarket'},
    'coles adelaide': {'lat': -34.9285, 'lon': 138.6007, 'state': 'SA', 'type': 'supermarket'},
    
    # Additional Australian Retail Chains
    'big w': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'kmart': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'bunnings': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'bunnings warehouse': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'officeworks': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'rebel sports': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    'supercheap auto': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'retail'},
    
    # Additional Food Chains
    'subway': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'domino\'s': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
    'pizza hut': {'lat': -33.8688, 'lon': 151.2093, 'state': 'NSW', 'type': 'fast_food'},
}
 
# State abbreviations
STATE_MAPPING: Dict[str, str] = {
    'nsw': 'NSW', 'new south wales': 'NSW',
    'vic': 'VIC', 'victoria': 'VIC',
    'qld': 'QLD', 'queensland': 'QLD',
    'wa': 'WA', 'western australia': 'WA',
    'sa': 'SA', 'south australia': 'SA',
    'tas': 'TAS', 'tasmania': 'TAS',
    'nt': 'NT', 'northern territory': 'NT',
    'act': 'ACT', 'australian capital territory': 'ACT'
}

# Centralized blacklist for NER post-processing (non-location tokens)
LOCATION_BLACKLIST: Set[str] = {
    'monday','tuesday','wednesday','thursday','friday','saturday','sunday',
    'january','february','march','april','may','june','july','august','september','october','november','december',
    'team','client','staff','office','meeting','dinner','lunch','breakfast','conference','seminar','training','party','event',
    'taxi','uber','flight','qantas','virgin','jetstar','trip',
    'at','to','from','in','on','for','with','the','a','an',
    'pty','ltd','inc','corp','hotel','cafe','restaurant','bar','motel','resort','inn',
    'christmas','easter','new','year','day','night','morning','afternoon','evening','week','month','annual','quarterly',
}

# Centralized country aliases mapping to ISO alpha-2 codes (lowercase)
COUNTRY_ALIASES: Dict[str, str] = {
    'uk': 'gb', 'u.k.': 'gb', 'united kingdom': 'gb', 'great britain': 'gb', 'britain': 'gb', 'england': 'gb',
    'usa': 'us', 'u.s.a.': 'us', 'u.s.': 'us', 'united states': 'us', 'america': 'us',
    'uae': 'ae', 'united arab emirates': 'ae', 'holland': 'nl',
}
