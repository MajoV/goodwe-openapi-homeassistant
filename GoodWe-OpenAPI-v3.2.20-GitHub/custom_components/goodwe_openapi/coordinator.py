"""GoodWe OpenAPI account discovery and plant-wide polling."""
import asyncio
import logging
import math
import time
import uuid
from datetime import timedelta, datetime, timezone
from collections import Counter, deque
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import API_URL, TOKEN_URL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


def walk(obj, depth=0):
    if depth > 12:
        return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            if isinstance(v, (dict, list)):
                yield from walk(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, depth + 1)


def sn_of(obj):
    for key in ('sn', 'deviceSn', 'deviceSN', 'serialNumber', 'deviceSerialNumber'):
        if isinstance(obj.get(key), str) and obj[key].strip():
            return obj[key].strip()
    return None


def extract_realtime(payload, sn):
    markers = {'pvPower', 'batteryPower', 'batterySoc1', 'acActivePower',
               'activePower', 'frequency', 'totalSellQ', 'refreshTime'}
    candidates = []
    for obj in walk(payload):
        score = len(markers.intersection(obj))
        if score:
            candidates.append((sn_of(obj) == sn, score, obj))
    if not candidates:
        raise UpdateFailed(f'No realtime fields for {sn}')
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


MODEL_KEYS = ('deviceModel', 'deviceModelName', 'modelName', 'model',
              'inverterModel', 'inverterType', 'productModel', 'productType',
              'deviceTypeName', 'modelType')


def extract_model(payload, sn):
    """Prefer model metadata attached to the matching inverter serial number."""
    candidates = []
    for obj in walk(payload):
        if not isinstance(obj, dict):
            continue
        matched = sn_of(obj) == sn
        for rank, field in enumerate(MODEL_KEYS):
            value = obj.get(field)
            if isinstance(value, str):
                value = value.strip()
                if value and value.lower() not in ('inverter', 'device', '1', 'unknown'):
                    candidates.append((matched, -rank, value))
    return max(candidates, default=(False, 0, None), key=lambda item: (item[0], item[1]))[2]


def extract_coordinates(record):
    """Read coordinates only when supplied by the existing plant discovery API."""
    if not isinstance(record, dict):
        return None
    for obj in (record, record.get('plantInfo'), record.get('location')):
        if not isinstance(obj, dict):
            continue
        for lat_key, lon_key in (
            ('latitude', 'longitude'), ('plantLatitude', 'plantLongitude'),
            ('plantLat', 'plantLng'), ('plantLat', 'plantLon'),
            ('lat', 'lng'), ('lat', 'lon'), ('pw_latitude', 'pw_longitude'),
        ):
            try:
                lat, lon = float(obj[lat_key]), float(obj[lon_key])
            except (KeyError, ValueError, TypeError):
                continue
            if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180 and (lat != 0 or lon != 0):
                return lat, lon
    return None


class GoodWeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.entry = entry
        self.hass = hass
        self.session = async_get_clientsession(hass)
        self.token = None
        self.token_expiry = 0
        self.last_discovery = 0
        self.plants = {}
        self.devices = {}
        self.discovery_message = 'Not started'
        self.limit = asyncio.Semaphore(2)
        self._realtime_warned = set()
        self._api_store = Store(hass, 1, f'goodwe_openapi_api_calls_{entry.entry_id}')
        self._api_loaded = False
        self._api_total = 0
        self._api_failed = 0
        self._api_by_endpoint = Counter()
        self._api_recent = deque()
        self._api_today = 0
        self._api_day = dt_util.now().date().isoformat()
        self._api_last_call = None
        interval = entry.options.get('scan_interval', DEFAULT_SCAN_INTERVAL)
        super().__init__(hass, _LOGGER, name='GoodWe OpenAPI account',
                         update_interval=timedelta(seconds=max(120, int(interval))))

    async def _load_api_stats(self):
        if self._api_loaded:
            return
        saved = await self._api_store.async_load() or {}
        self._api_total = int(saved.get('total', 0))
        self._api_failed = int(saved.get('failed', 0))
        self._api_by_endpoint = Counter(saved.get('by_endpoint', {}))
        self._api_day = saved.get('day', dt_util.now().date().isoformat())
        self._api_today = int(saved.get('today', 0))
        self._api_last_call = saved.get('last_call')
        self._api_recent = deque(float(t) for t in saved.get('recent', [])
                                 if isinstance(t, (float, int)))
        self._api_prune()
        self._api_loaded = True

    def _api_prune(self):
        cutoff = time.time() - 3600
        while self._api_recent and self._api_recent[0] <= cutoff:
            self._api_recent.popleft()
        today = dt_util.now().date().isoformat()
        if today != self._api_day:
            self._api_day = today
            self._api_today = 0

    def _api_record(self, endpoint, success):
        self._api_prune()
        now = datetime.now(timezone.utc)
        self._api_total += 1
        self._api_today += 1
        self._api_recent.append(now.timestamp())
        self._api_by_endpoint[endpoint] += 1
        self._api_last_call = now.isoformat()
        if not success:
            self._api_failed += 1

    def api_stats(self):
        self._api_prune()
        return {'total': self._api_total, 'failed': self._api_failed,
                'today': self._api_today, 'hour': len(self._api_recent),
                'last_call': self._api_last_call,
                'by_endpoint': dict(self._api_by_endpoint)}

    async def _save_api_stats(self):
        await self._api_store.async_save({
            'total': self._api_total, 'failed': self._api_failed,
            'today': self._api_today, 'day': self._api_day,
            'recent': list(self._api_recent), 'last_call': self._api_last_call,
            'by_endpoint': dict(self._api_by_endpoint)})

    async def _token(self):
        if self.token and time.monotonic() < self.token_expiry:
            return self.token
        success = False
        try:
            async with asyncio.timeout(30):
                async with self.session.post(TOKEN_URL,
                    auth=aiohttp.BasicAuth(self.entry.data['client_id'], self.entry.data['client_secret']),
                    data={'grant_type': 'client_credentials'}) as resp:
                    data = await resp.json(content_type=None)
                    success = (200 <= resp.status < 300 and isinstance(data, dict)
                               and bool(data.get('access_token')))
                    if not success:
                        raise UpdateFailed(f'OAuth failed HTTP {resp.status}')
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise UpdateFailed(f'OAuth network failure: {exc}') from exc
        finally:
            self._api_record('oauth/token', success)
        self.token = data['access_token']
        self.token_expiry = time.monotonic() + max(30, int(data.get('expires_in', 3600)) - 90)
        return self.token

    async def _post(self, path, body):
        async with self.limit:
            for attempt in range(2):
                token = await self._token()
                success = False
                try:
                    async with asyncio.timeout(35):
                        async with self.session.post(f'{API_URL}/{path}', json=body,
                            headers={'Authorization': f'Bearer {token}', 'Request-Id': str(uuid.uuid4())}) as resp:
                            result = await resp.json(content_type=None)
                            if resp.status == 401 and attempt == 0:
                                self.token = None
                                continue
                            if not isinstance(result, dict) or not 200 <= resp.status < 300 or str(result.get('code')) != '00000':
                                code = result.get('code') if isinstance(result, dict) else 'invalid response'
                                raise UpdateFailed(f'{path}: HTTP {resp.status}, code {code}')
                            success = True
                            return result.get('data', result)
                except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
                    raise UpdateFailed(f'{path}: {exc}') from exc
                finally:
                    self._api_record(path, success)
            raise UpdateFailed('Authorization rejected')

    async def _plant_ids(self):
        """Only explicitly selected Plant IDs; no packaged file or auto-import."""
        return list(dict.fromkeys(self.entry.options.get('selected_plant_ids', [])))

    async def _discover(self):
        """Find devices by exact Plant ID (searchType 1), up to 100 IDs per call."""
        ids = await self._plant_ids()
        plants = {}
        devices = {}
        errors = []
        returned = set()
        for offset in range(0, len(ids), 100):
            batch = ids[offset:offset + 100]
            try:
                response = await self._post('base-info/plant/devices', {
                    'searchType': 1, 'searchKey': batch})
            except UpdateFailed as exc:
                errors.append(f'batch {offset // 100 + 1}: {exc}')
                continue
            # Documented response: data=[{plantId, plantName, deviceData:[...]}].
            # Some GoodWe errors use data=[{plantData:[], noPermissionSearchKey:[]}].
            for record in walk(response):
                pid = record.get('plantId')
                if not isinstance(pid, str) or pid.lower() not in batch:
                    continue
                pid = pid.lower()
                returned.add(pid)
                name = record.get('plantName') or pid
                plant_info = {'plantId': pid, 'plantName': name}
                coords = extract_coordinates(record)
                if coords is not None:
                    plant_info.update(latitude=coords[0], longitude=coords[1])
                elif pid in self.plants:
                    for field in ('latitude', 'longitude'):
                        if field in self.plants[pid]:
                            plant_info[field] = self.plants[pid][field]
                plants[pid] = plant_info
                device_data = record.get('deviceData', [])
                if not isinstance(device_data, list):
                    continue
                for device in device_data:
                    if not isinstance(device, dict):
                        continue
                    sn = sn_of(device)
                    try:
                        dtype = int(device.get('deviceType'))
                    except (TypeError, ValueError):
                        continue
                    if sn and dtype in (1, 6):
                        model = extract_model(device, sn)
                        devices[(pid, dtype, sn)] = {
                            'sn': sn, 'type': dtype, 'plant_id': pid, 'plant_name': name,
                            'model': model or self.devices.get((pid, dtype, sn), {}).get('model')}
        # /base-info/plant/devices does not include GPS. The /base-info/plants
        # response contains latitude/longitude in data.plantData.
        # Query only explicitly selected Plant IDs, once per discovery cycle.
        async def lookup_plant_locations():
            unresolved = set(plants)
            for offset in range(0, len(ids), 100):
                batch = ids[offset:offset + 100]
                try:
                    response = await self._post('base-info/plants', {
                        'searchKey': batch, 'searchType': 1, 'plantType': 1,
                        'pageIndex': 1, 'pageSize': 100})
                except UpdateFailed as exc:
                    _LOGGER.warning('GoodWe plant GPS lookup failed: %s', exc)
                    continue
                for record in walk(response):
                    pid = record.get('plantId')
                    if not isinstance(pid, str) or pid.lower() not in unresolved:
                        continue
                    coords = extract_coordinates(record)
                    if coords is not None:
                        plants[pid.lower()].update(latitude=coords[0], longitude=coords[1])
                        unresolved.discard(pid.lower())
            # Some accounts may not support searching plant details by ID.
            # Fall back to exact known plant name, verifying returned Plant ID.
            for pid in list(unresolved):
                name = plants[pid].get('plantName')
                if not name:
                    continue
                try:
                    response = await self._post('base-info/plants', {
                        'searchKey': [name], 'searchType': 0, 'plantType': 1,
                        'pageIndex': 1, 'pageSize': 100})
                except UpdateFailed as exc:
                    _LOGGER.debug('GoodWe GPS lookup for %s failed: %s', pid, exc)
                    continue
                for record in walk(response):
                    if str(record.get('plantId', '')).lower() != pid:
                        continue
                    coords = extract_coordinates(record)
                    if coords is not None:
                        plants[pid].update(latitude=coords[0], longitude=coords[1])
                        break

        if plants:
            await lookup_plant_locations()
        # On transient discovery failure, retain only currently selected plants.
        selected = set(ids)
        for pid, old in self.plants.items():
            if pid in selected and pid not in plants:
                plants[pid] = old
        for key, old in self.devices.items():
            if key[0] in selected and key not in devices and key[0] not in returned:
                devices[key] = old
        # The plant/device listing often omits the inverter model. Query the
        # dedicated device information endpoint only for inverters without one.
        # Cache discovered models across the 6-hour discovery cycle.
        missing = [(key, info) for key, info in devices.items()
                   if info['type'] == 1 and not info.get('model')]

        async def fetch_model(key, info):
            try:
                response = await self._post('base-info/device/info', {
                    'sns': [info['sn']], 'deviceType': 1})
                return key, extract_model(response, info['sn'])
            except UpdateFailed as exc:
                _LOGGER.debug('GoodWe model lookup %s: %s', info['sn'], exc)
                return key, None

        if missing:
            model_results = await asyncio.gather(
                *(fetch_model(key, info) for key, info in missing))
            for key, model in model_results:
                if model:
                    devices[key]['model'] = model
        self.plants = plants
        self.devices = devices
        self.discovery_message = (
            f'{len(returned)}/{len(ids)} requested plant IDs returned this cycle; '
            f'{len(self.devices)} devices retained; {len(errors)} API batch errors')
        self.last_discovery = time.monotonic()
        _LOGGER.info('GoodWe Plant ID discovery: %s', self.discovery_message)
        if errors:
            _LOGGER.warning('GoodWe Plant ID discovery errors: %s', '; '.join(errors))
        if ids and not returned:
            _LOGGER.warning('GoodWe returned no plants for the provided Plant IDs. '
                            'Check searchType=1 permissions and response schema.')

    async def _fetch(self, key, info):
        try:
            payload = await self._post('realtime/devices', {
                'sns': [info['sn']], 'deviceType': info['type']})
            value = extract_realtime(payload, info['sn'])
            self._realtime_warned.discard(key)
            return key, value
        except UpdateFailed as exc:
            if key not in self._realtime_warned:
                _LOGGER.debug('GoodWe %s: %s (further debug messages suppressed until recovery)', info['sn'], exc)
                self._realtime_warned.add(key)
            return key, None

    async def _async_update_data(self):
        await self._load_api_stats()
        try:
            return await self._update_goodwe_data()
        finally:
            await self._save_api_stats()

    async def _update_goodwe_data(self):
        if not self.last_discovery or time.monotonic() - self.last_discovery >= 21600:
            try:
                await self._discover()
            except UpdateFailed as exc:
                _LOGGER.warning('GoodWe discovery failed: %s', exc)
                self.last_discovery = time.monotonic()
        results = await asyncio.gather(*(self._fetch(key, info) for key, info in self.devices.items()))
        values = {key: value for key, value in results if value is not None}
        return {'devices': dict(self.devices), 'values': values,
                'plants': dict(self.plants), 'discovery': self.discovery_message}
