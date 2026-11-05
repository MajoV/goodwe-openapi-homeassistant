"""GoodWe account configured once; Plant IDs managed via integration Options."""
import asyncio
import uuid
import re
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, TOKEN_URL, DEFAULT_SCAN_INTERVAL
from .coordinator import GoodWeCoordinator, walk, sn_of

CREDENTIALS = vol.Schema({
    vol.Required('client_id'): str,
    vol.Required('client_secret'): str,
    vol.Optional('scan_interval', default=DEFAULT_SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=120)),
})

def valid_plant_id(value):
    try:
        return str(uuid.UUID(value.strip()))
    except (ValueError, AttributeError, TypeError):
        raise vol.Invalid('invalid_plant_id')

class GoodWeOpenAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 4

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                async with asyncio.timeout(25):
                    session = async_get_clientsession(self.hass)
                    async with session.post(TOKEN_URL, auth=aiohttp.BasicAuth(
                        user_input['client_id'], user_input['client_secret']),
                        data={'grant_type': 'client_credentials'}) as response:
                        body = await response.json(content_type=None)
                        if not 200 <= response.status < 300 or not isinstance(body, dict) or not body.get('access_token'):
                            errors['base'] = 'invalid_auth'
            except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
                errors['base'] = 'cannot_connect'
            if not errors:
                await self.async_set_unique_id(user_input['client_id'].strip())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title='GoodWe OpenAPI by home-co', data=user_input)
        return self.async_show_form(step_id='user', data_schema=CREDENTIALS, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GoodWeOptionsFlow()

class GoodWeOptionsFlow(config_entries.OptionsFlow):
    def _ids(self):
        return list(self.config_entry.options.get('selected_plant_ids', []))

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(step_id='init', menu_options=['add_plant', 'edit_client_number', 'find_plant_by_sn', 'remove_plant', 'settings'])

    async def async_step_add_plant(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                pid = valid_plant_id(user_input['plant_id'])
                ids = self._ids()
                if pid in ids:
                    errors['base'] = 'already_added'
                else:
                    ids.append(pid)
                    return self.async_create_entry(title='', data={**self.config_entry.options, 'selected_plant_ids': ids, 'client_numbers': {**self.config_entry.options.get('client_numbers', {}), pid: user_input.get('client_number', '').strip()}})
            except vol.Invalid:
                errors['base'] = 'invalid_plant_id'
        return self.async_show_form(step_id='add_plant', data_schema=vol.Schema({vol.Required('plant_id'): str, vol.Optional('client_number', default=''): vol.All(str, vol.Match(r'^(?:[0-9]{4})?$'))}), errors=errors)

    async def async_step_edit_client_number(self, user_input=None):
        ids = self._ids()
        if not ids:
            return self.async_abort(reason='no_plants')
        if user_input is not None:
            numbers = dict(self.config_entry.options.get('client_numbers', {}))
            numbers[user_input['plant_id']] = user_input['client_number'].strip()
            return self.async_create_entry(title='', data={**self.config_entry.options, 'client_numbers': numbers})
        return self.async_show_form(step_id='edit_client_number', data_schema=vol.Schema({
            vol.Required('plant_id'): vol.In({pid: pid for pid in ids}),
            vol.Required('client_number'): vol.All(str, vol.Match(r'^[0-9]{4}$')),
        }))

    async def async_step_find_plant_by_sn(self, user_input=None):
        """Find inverter SN in selected plants using the confirmed Plant ID endpoint."""
        errors = {}
        if user_input is not None:
            sn = user_input['inverter_sn'].strip().upper()
            coordinator = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
            if coordinator is None:
                errors['base'] = 'cannot_connect'
            else:
                try:
                    ids = self._ids()
                    if not ids:
                        return self.async_show_form(
                            step_id='find_plant_result',
                            description_placeholders={'result': 'No selected plants. Add a Plant ID first.'},
                        )
                    found = {}
                    for offset in range(0, len(ids), 100):
                        batch = ids[offset:offset + 100]
                        result = await coordinator._post('base-info/plant/devices', {
                            'searchType': 1, 'searchKey': batch})
                        for record in walk(result):
                            pid = str(record.get('plantId', '')).lower()
                            if pid not in batch or not isinstance(record.get('deviceData'), list):
                                continue
                            for device in record['deviceData']:
                                if (isinstance(device, dict)
                                        and str(device.get('deviceType')) == '1'
                                        and (sn_of(device) or '').upper() == sn):
                                    found[pid] = str(record.get('plantName') or pid)
                    if found:
                        result_text = '\n'.join(f'{name} — {pid}' for pid, name in found.items())
                    else:
                        result_text = ('No matching inverter among selected plants. '
                                       'Searching unselected account plants is not supported by this lookup.')
                    return self.async_show_form(
                        step_id='find_plant_result',
                        description_placeholders={'result': result_text},
                    )
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning('GoodWe SN lookup failed: %s', exc)
                    errors['base'] = 'lookup_failed'
        return self.async_show_form(step_id='find_plant_by_sn', data_schema=vol.Schema({
            vol.Required('inverter_sn'): vol.All(str, vol.Length(min=1, max=100))
        }), errors=errors)

    async def async_step_find_plant_result(self, user_input=None):
        return self.async_abort(reason='lookup_complete')

    async def async_step_remove_plant(self, user_input=None):
        ids = self._ids()
        if not ids:
            return self.async_abort(reason='no_plants')
        if user_input is not None:
            ids.remove(user_input['plant_id'])
            numbers = dict(self.config_entry.options.get('client_numbers', {}))
            numbers.pop(user_input['plant_id'], None)
            return self.async_create_entry(title='', data={**self.config_entry.options, 'selected_plant_ids': ids, 'client_numbers': numbers})
        return self.async_show_form(step_id='remove_plant', data_schema=vol.Schema({
            vol.Required('plant_id'): vol.In({pid: pid for pid in ids})
        }))

    async def async_step_settings(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title='', data={**self.config_entry.options, **user_input})
        return self.async_show_form(step_id='settings', data_schema=vol.Schema({
            vol.Required('scan_interval', default=self.config_entry.options.get(
                'scan_interval', self.config_entry.data.get('scan_interval', DEFAULT_SCAN_INTERVAL))):
                vol.All(vol.Coerce(int), vol.Range(min=120))
        }))
