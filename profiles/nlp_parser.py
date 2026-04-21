import re

def parse_query(query):
    """
    Convert plain English query into a dictionary of filters.
    Returns None if no filters can be extracted.
    """
    query = query.lower().strip()
    filters = {}

    # Gender
    if 'male' in query:
        filters['gender'] = 'male'
    elif 'female' in query:
        filters['gender'] = 'female'

    # Age group
    if 'child' in query or 'children' in query:
        filters['age_group'] = 'child'
    elif 'teenager' in query or 'teens' in query:
        filters['age_group'] = 'teenager'
    elif 'adult' in query:
        filters['age_group'] = 'adult'
    elif 'senior' in query or 'old' in query:
        filters['age_group'] = 'senior'

    # "young" maps to age 16-24
    if 'young' in query:
        filters['min_age'] = 16
        filters['max_age'] = 24

    # Numeric age ranges
    match = re.search(r'above (\d+)', query)
    if match:
        filters['min_age'] = int(match.group(1))
    match = re.search(r'below (\d+)', query)
    if match:
        filters['max_age'] = int(match.group(1))
    match = re.search(r'between (\d+) and (\d+)', query)
    if match:
        filters['min_age'] = int(match.group(1))
        filters['max_age'] = int(match.group(2))

    # Country mapping (extend as needed)
    country_map = {
        'nigeria': 'NG', 'kenya': 'KE', 'south africa': 'ZA', 'ghana': 'GH',
        'angola': 'AO', 'ethiopia': 'ET', 'morocco': 'MA', 'egypt': 'EG',
        'tanzania': 'TZ', 'uganda': 'UG', 'rwanda': 'RW', 'congo': 'CD',
        'cameroon': 'CM', 'senegal': 'SN'
    }
    for country_name, code in country_map.items():
        if country_name in query:
            filters['country_id'] = code
            break

    # If no filters at all, return None
    return filters if filters else None