from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import DOMAIN
from .coordinator import GoodWeCoordinator

PLATFORMS = ['sensor', 'device_tracker']

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = GoodWeCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Remove only registry records belonging to explicitly deselected plants."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        selected = {str(pid).lower() for pid in entry.options.get('selected_plant_ids', [])}
        previous = set(coordinator.plants) | {key[0] for key in coordinator.devices}
        removed = previous - selected
        if removed:
            entities = er.async_get(hass)
            devices = dr.async_get(hass)
            # Remove entities first, then their device records. Limit the scope
            # to this config entry and exact plant IDs.
            for entity in list(er.async_entries_for_config_entry(entities, entry.entry_id)):
                uid = entity.unique_id.lower()
                if any(uid.startswith(pid + '_') or uid == f'goodwe_plant_location_{pid}' for pid in removed):
                    entities.async_remove(entity.entity_id)
            for device in list(dr.async_entries_for_config_entry(devices, entry.entry_id)):
                if any(identifier[0] == DOMAIN and any(
                        identifier[1].lower().startswith(pid + ':') for pid in removed)
                        for identifier in device.identifiers):
                    devices.async_remove_device(device.id)
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
