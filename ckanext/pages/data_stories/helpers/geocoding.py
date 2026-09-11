"""Búsquedas explícitas de lugares, con caché y cupo compartido entre workers."""
import hashlib
import json
import math

import requests
from ckan.plugins import toolkit as tk
from ckan.lib.redis import connect_to_redis


class GeocodingError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


def search_locations(args):
    query = ' '.join((args.get('q') or '').split())
    if not 2 <= len(query) <= 200:
        raise GeocodingError('Enter a place name between 2 and 200 characters.', 400)
    params = {'q': query, 'format': 'geojson', 'limit': 8, 'bounded': 0}
    if args.get('viewbox'):
        try:
            values = [float(v) for v in args['viewbox'].split(',')]
            if len(values) != 4 or any(not math.isfinite(v) or abs(v) > (180 if i % 2 == 0 else 90) for i, v in enumerate(values)):
                raise ValueError()
        except (ValueError, TypeError):
            raise GeocodingError('Invalid map bounds.', 400)
        params['viewbox'] = ','.join(str(round(v, 2)) for v in values)
    endpoint = tk.config.get('ckanext.data_stories.geocoder_url', 'https://nominatim.openstreetmap.org/search')
    key = 'data-stories:geocode:' + hashlib.sha256((endpoint + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    try:
        redis = connect_to_redis()
        cached = redis.get(key)
        if cached:
            return json.loads(cached)
        if not redis.set('data-stories:geocode:upstream-slot', '1', nx=True, px=1100):
            raise GeocodingError('Please wait a moment before searching again.', 429)
    except GeocodingError:
        raise
    except Exception:
        raise GeocodingError('Location search is temporarily unavailable.', 503)
    try:
        response = requests.get(endpoint, params=params, timeout=8, headers={
            'User-Agent': 'IHP-WINS location search (' + tk.config.get('ckan.site_url', '') + ')',
            'Accept': 'application/geo+json, application/json',
        })
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
            raise ValueError('Invalid geocoder response')
    except (requests.RequestException, ValueError):
        raise GeocodingError('Location search is temporarily unavailable.', 502)
    try:
        redis.setex(key, 86400, json.dumps(data))
    except Exception:
        pass
    return data
