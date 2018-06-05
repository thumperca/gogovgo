"""
Google Geocode API to validate postal code
and find county for selected postal_code and state combination
"""
import requests


API_KEY = 'AIzaSyBP53neYKF_Dmp09Hs5Hjz1mgWAy4bUj-Y'
API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'


def get_location_info(zipcode):
    """Returns location information for a US zipcode"""
    params = '?address={},USkey={}'.format(zipcode, API_KEY)
    url = API_URL + params
    response = requests.get(url)
    if response.status_code != 200:
        return

    json = response.json()
    if json['status'] != 'OK':
        return

    for entry in json['results']:
        if 'postal_code' not in entry['types']:
            continue
        data = {}
        for component in entry['address_components']:
            data[component['types'][0]] = component['short_name']

        if not data or data.get('postal_code') != zipcode or data.get('country') != 'US':
            continue

        return {
            'county':  (data.get('administrative_area_level_2', '') or '').replace(' County', ''),
            'state': data.get('administrative_area_level_1'),
            'latitude': entry['geometry']['location']['lat'],
            'longitude': entry['geometry']['location']['lng']
        }


def get_county(postal_code, state):
    """
    Get county name for given postal_code & state

    Args:
        postal_code/str: Postal code provided by reviewer
        state/str: State selected by reviewer e.g. CA (for California) or ND (for North Dakota)

    Returns:
        str: county name for given for given combination if it's valid
        None: if the postal_code, state or the combination is invalid

    """
    params = '?address={},{}&key={}'.format(postal_code, state, API_KEY)
    url = API_URL + params
    response = requests.get(url)
    if response.status_code != 200:
        return

    json = response.json()
    if json['status'] != 'OK':
        return

    for entry in json['results']:
        if 'postal_code' not in entry['types']:
            continue
        data = {}
        for component in entry['address_components']:
            data[component['types'][0]] = component['short_name']

        if not data:
            continue
        if data.get('country') != 'US':
            # or data.get('administrative_area_level_1') != state:
            continue
        if data.get('postal_code') != postal_code:
            continue

        county = data.get('administrative_area_level_2', '').replace(' County', '')
        return county
