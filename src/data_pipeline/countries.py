"""European country bounding boxes for MERRA-2 data subsetting.

Bounding boxes are (lon_min, lat_min, lon_max, lat_max).
"""

COUNTRIES = {
    'germany': (5.988, 47.302, 15.016, 54.983),
    'france': (-5.142, 42.333, 8.231, 51.089),
    'spain': (-9.301, 36.000, 3.315, 43.791),
    'italy': (6.627, 36.649, 18.520, 47.092),
    'uk': (-8.182, 49.959, 1.769, 58.635),
    'united_kingdom': (-8.182, 49.959, 1.769, 58.635),
    'poland': (14.123, 49.002, 24.146, 54.836),
    'netherlands': (3.358, 50.751, 7.210, 53.472),
    'belgium': (2.546, 49.497, 6.404, 51.505),
    'austria': (9.531, 46.372, 17.161, 49.021),
    'switzerland': (5.956, 45.818, 10.492, 47.808),
    'portugal': (-9.500, 36.960, -6.189, 42.154),
    'sweden': (11.109, 55.337, 24.167, 69.060),
    'norway': (4.650, 57.960, 31.078, 71.185),
    'finland': (20.649, 59.808, 31.587, 70.092),
    'denmark': (8.089, 54.568, 15.159, 57.752),
    'ireland': (-10.478, 51.422, -5.998, 55.380),
    'czech_republic': (12.091, 48.552, 18.859, 51.058),
    'czechia': (12.091, 48.552, 18.859, 51.058),
    'romania': (20.262, 43.619, 29.691, 48.265),
    'hungary': (16.112, 45.737, 22.898, 48.585),
    'greece': (19.374, 34.802, 29.645, 41.749),
    'croatia': (13.490, 42.393, 19.427, 46.555),
    'bulgaria': (22.357, 41.236, 28.612, 44.215),
    'slovakia': (16.847, 47.728, 22.558, 49.603),
    'slovenia': (13.383, 45.421, 16.607, 46.877),
    'luxembourg': (5.734, 49.448, 6.531, 50.183),
    'estonia': (21.774, 57.516, 28.210, 59.676),
    'latvia': (20.971, 55.675, 28.241, 58.082),
    'lithuania': (20.932, 53.901, 26.836, 56.450),
    'europe': (-11.000, 34.000, 32.000, 72.000),
}

# Standard UTC timezone offsets for each country
TIMEZONES = {
    'germany': 1, 'france': 1, 'spain': 1, 'italy': 1,
    'uk': 0, 'united_kingdom': 0, 'ireland': 0, 'portugal': 0,
    'poland': 1, 'netherlands': 1, 'belgium': 1,
    'austria': 1, 'switzerland': 1, 'luxembourg': 1,
    'denmark': 1, 'sweden': 1, 'norway': 1,
    'czech_republic': 1, 'czechia': 1,
    'hungary': 1, 'croatia': 1, 'slovenia': 1, 'slovakia': 1,
    'romania': 2, 'bulgaria': 2, 'greece': 2,
    'finland': 2, 'estonia': 2, 'latvia': 2, 'lithuania': 2,
    'europe': 1,  # default CET for pan-European
}

# Map alternate/native-language country names to canonical COUNTRIES keys
COUNTRY_ALIASES = {
    # German names
    "deutschland": "germany",
    "frankreich": "france",
    "oesterreich": "austria",
    "osterreich": "austria",
    "österreich": "austria",
    "schweiz": "switzerland",
    "niederlande": "netherlands",
    "belgien": "belgium",
    "polen": "poland",
    "schweden": "sweden",
    "norwegen": "norway",
    "finnland": "finland",
    "dänemark": "denmark",
    "daenemark": "denmark",
    "irland": "ireland",
    "tschechien": "czechia",
    "tschechische_republik": "czechia",
    "rumänien": "romania",
    "rumaenien": "romania",
    "ungarn": "hungary",
    "griechenland": "greece",
    "kroatien": "croatia",
    "bulgarien": "bulgaria",
    "slowakei": "slovakia",
    "slowenien": "slovenia",
    "luxemburg": "luxembourg",
    "estland": "estonia",
    "lettland": "latvia",
    "litauen": "lithuania",
    "spanien": "spain",
    "italien": "italy",
    # English alternates
    "great_britain": "uk",
    "the_netherlands": "netherlands",
    "holland": "netherlands",
    # French names
    "allemagne": "germany",
    "autriche": "austria",
    "suisse": "switzerland",
    "pays-bas": "netherlands",
    "pays_bas": "netherlands",
    "belgique": "belgium",
    "pologne": "poland",
    "suède": "sweden",
    "suede": "sweden",
    "norvège": "norway",
    "norvege": "norway",
    "finlande": "finland",
    "danemark": "denmark",
    "irlande": "ireland",
    "tchéquie": "czechia",
    "tchequie": "czechia",
    "république_tchèque": "czechia",
    "republique_tcheque": "czechia",
    "roumanie": "romania",
    "hongrie": "hungary",
    "grèce": "greece",
    "grece": "greece",
    "croatie": "croatia",
    "bulgarie": "bulgaria",
    "slovaquie": "slovakia",
    "slovénie": "slovenia",
    "slovenie": "slovenia",
    "estonie": "estonia",
    "lettonie": "latvia",
    "lituanie": "lithuania",
    "espagne": "spain",
    "italie": "italy",
    "royaume-uni": "uk",
    "royaume_uni": "uk",
}


def normalize_country(country):
    """Normalize user-provided country strings to internal keys, resolving aliases."""
    key = '_'.join(country.strip().lower().split())
    return COUNTRY_ALIASES.get(key, key)


def get_bbox(country):
    """Get bounding box for a country.

    Returns:
        Tuple of (lon_min, lat_min, lon_max, lat_max)
    """
    key = normalize_country(country)
    if key not in COUNTRIES:
        available = ', '.join(sorted(COUNTRIES.keys()))
        raise ValueError(f"Unknown country: '{country}'. Available: {available}")
    return COUNTRIES[key]


def get_timezone(country):
    """Get UTC timezone offset for a country.

    Returns:
        Integer UTC offset (e.g., 1 for CET, 2 for EET).
    """
    key = normalize_country(country)
    if key in TIMEZONES:
        return TIMEZONES[key]
    # Fallback: estimate from country bbox center longitude
    if key in COUNTRIES:
        lon_min, _, lon_max, _ = COUNTRIES[key]
        return round((lon_min + lon_max) / 2 / 15)
    return 0


def list_countries():
    """List all available countries."""
    return sorted(COUNTRIES.keys())
