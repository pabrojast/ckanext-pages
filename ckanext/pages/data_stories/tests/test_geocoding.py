import json
from unittest.mock import Mock

import pytest
from ckanext.pages.data_stories.helpers import geocoding as geo


@pytest.fixture
def service(monkeypatch):
    redis = Mock()
    redis.get.return_value = None
    redis.set.return_value = True
    response = Mock()
    response.json.return_value = {'type': 'FeatureCollection', 'features': []}
    request = Mock(return_value=response)
    monkeypatch.setattr(geo, 'connect_to_redis', lambda: redis)
    monkeypatch.setattr(geo.requests, 'get', request)
    return redis, request


def test_upstream_request_is_bounded_identified_and_cached(service):
    redis, request = service
    result = geo.search_locations({'q': '  Accra  ', 'viewbox': '-4,10,4,0', 'url': 'https://untrusted.invalid'})
    assert result['features'] == []
    args, kwargs = request.call_args
    assert args[0] == 'https://nominatim.openstreetmap.org/search'
    assert kwargs['params'] == {'q': 'Accra', 'format': 'geojson', 'limit': 8, 'bounded': 0, 'viewbox': '-4.0,10.0,4.0,0.0'}
    assert 'IHP-WINS' in kwargs['headers']['User-Agent']
    assert redis.set.call_args.kwargs == {'nx': True, 'px': 1100}
    assert redis.setex.call_args.args[1] == 86400


def test_cache_hit_does_not_consume_slot_or_call_upstream(service):
    redis, request = service
    redis.get.return_value = json.dumps({'type': 'FeatureCollection', 'features': []})
    geo.search_locations({'q': 'Accra'})
    request.assert_not_called()
    redis.set.assert_not_called()


@pytest.mark.parametrize('args', [{'q': 'x'}, {'q': 'x' * 201}, {'q': 'Accra', 'viewbox': 'nan,0,1,2'}, {'q': 'Accra', 'viewbox': '1,2,3'}, {'q': 'Accra', 'viewbox': '0,100,0,0'}])
def test_invalid_requests_never_reach_upstream(service, args):
    with pytest.raises(geo.GeocodingError) as error:
        geo.search_locations(args)
    assert error.value.status == 400
    service[1].assert_not_called()


def test_rate_limit_and_cache_outage_fail_closed(service, monkeypatch):
    redis, request = service
    redis.set.return_value = False
    with pytest.raises(geo.GeocodingError) as error:
        geo.search_locations({'q': 'Accra'})
    assert error.value.status == 429
    redis.get.side_effect = RuntimeError('Redis unavailable')
    with pytest.raises(geo.GeocodingError) as error:
        geo.search_locations({'q': 'Accra'})
    assert error.value.status == 503
    request.assert_not_called()


def test_invalid_upstream_response_is_not_cached(service):
    redis, request = service
    request.return_value.json.return_value = {'error': 'unavailable'}
    with pytest.raises(geo.GeocodingError) as error:
        geo.search_locations({'q': 'Accra'})
    assert error.value.status == 502
    redis.setex.assert_not_called()
