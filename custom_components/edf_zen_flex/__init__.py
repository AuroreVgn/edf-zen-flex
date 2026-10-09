"""Intégration EDF Zen Flex pour Home Assistant."""
from datetime import timedelta
from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_utc_time_change, async_track_time_change
from .const import DEFAULT_INTERVAL
from .const import DOMAIN
from .coordinator import ZenCoordinator

async def async_setup_entry(hass, entry):
    coordinator = ZenCoordinator(hass, entry)
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR, Platform.BUTTON])
    @callback
    def local_tick(now):
        # Recalcul HP/HC et jour civil chaque minute, sans nouvel appel EDF
        # et sans repousser l’échéance réseau du coordinateur.
        coordinator.async_update_listeners()
    entry.async_on_unload(async_track_utc_time_change(hass, local_tick, second=0))
    # Daily local-time check, separate from the status polling and tariff import.
    @callback
    def tariff_tick(now):
        hass.async_create_task(coordinator.async_check_published_tariffs())
    entry.async_on_unload(async_track_time_change(hass, tariff_tick, hour=10, minute=0, second=0))
    # Première vérification au démarrage : ne pas attendre 10 h le lendemain.
    hass.async_create_task(coordinator.async_check_published_tariffs())
    return True

async def async_options_updated(hass, entry):
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        await hass.config_entries.async_reload(entry.entry_id)
        return
    coordinator.entry = entry
    coordinator.update_interval = timedelta(minutes=coordinator.settings.get("interval", DEFAULT_INTERVAL))
    # Publier immédiatement les nouveaux calculs, même si EDF est indisponible.
    # Aucun rechargement réseau n’est nécessaire pour valider des prix locaux.
    coordinator.async_update_listeners()

async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR, Platform.BUTTON]):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False
