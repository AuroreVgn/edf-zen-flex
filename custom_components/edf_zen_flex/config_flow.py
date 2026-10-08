"""Configuration initiale et options en trois écrans."""
from datetime import datetime, timedelta
import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector
from .api import fetch
from .tariffs import fetch_published_tariffs
from .const import DOMAIN, DEFAULT_INTERVAL
from .model import PARIS, DEFAULT_HC, TARIFF_KEYS, REFERENCE_RATES, REFERENCE_SOURCE, validate_settings


def interval_schema(default):
    return vol.Schema({vol.Required("interval", default=default): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440))})


def tariff_schema(values, allow_import=True):
    fields = {vol.Required(key, default=values.get(key, REFERENCE_RATES[key])):
              vol.All(vol.Coerce(float), vol.Range(min=0, max=10)) for key in TARIFF_KEYS}
    fields.update({
        vol.Required("import_published_tariffs", default=False): bool,
        vol.Required("tariffs_confirmed", default=values.get("tariffs_confirmed", False)): bool,
        vol.Required("tariff_date", default=values.get("tariff_date", "2026-09-15")): selector.DateSelector(),
        vol.Required("tariff_source", default=values.get("tariff_source", REFERENCE_SOURCE)): str,
        vol.Required("hc_periods", default=values.get("hc_periods", DEFAULT_HC)): str,
    })
    if not allow_import:
        fields.pop(next(key for key in fields if str(key) == "import_published_tariffs"))
    return vol.Schema(fields)


def history_schema(values):
    today = datetime.now(PARIS).date()
    yesterday = today - timedelta(days=1)
    default_date = yesterday if yesterday.year == today.year else today
    return vol.Schema({
        vol.Required("baseline_enabled", default=values.get("baseline_enabled", False)): bool,
        vol.Required("baseline_date", default=values.get("baseline_date", default_date.isoformat())): selector.DateSelector(),
        vol.Required("baseline_bonus_count", default=values.get("baseline_bonus_count", 0)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=366)),
        vol.Required("baseline_count", default=values.get("baseline_count", 0)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=20)),
    })


class SettingsSteps:
    """Collecte transactionnelle : les options sont enregistrées au dernier écran."""
    _allow_import = True

    async def async_step_tariffs(self, user_input=None):
        errors = {}
        if user_input is not None and user_input.get("import_published_tariffs"):
            try:
                reference = await fetch_published_tariffs(async_get_clientsession(self.hass))
            except (ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_import_tariffs"
            else:
                self._values.update({k:v for k,v in user_input.items() if k != "import_published_tariffs"})
                self._values.update(reference)
            # Réafficher les prix importés, confirmation décochée, avant enregistrement.
            return self.async_show_form(step_id="tariffs", data_schema=tariff_schema(self._values, self._allow_import), errors=errors)
        if user_input is not None:
            candidate = {**self._values, **{k:v for k,v in user_input.items() if k != "import_published_tariffs"}}
            try:
                # Un ancien compteur initial sera ajusté à l’écran suivant.
                validate_settings({**candidate, "baseline_enabled": False}, datetime.now(PARIS).date())
            except (ValueError, KeyError):
                errors["base"] = "invalid_tariffs"
            else:
                if not candidate.get("tariffs_confirmed"):
                    errors["base"] = "tariffs_not_confirmed"
                else:
                    self._values = candidate
                    return await self._finish_tariffs()
        return self.async_show_form(step_id="tariffs", data_schema=tariff_schema({**self._values, **(user_input or {})}, self._allow_import), errors=errors)

    async def _finish_tariffs(self):
        return await self.async_step_history()

    async def async_step_history(self, user_input=None):
        errors = {}
        if user_input is not None:
            candidate = {**self._values, **user_input}
            try:
                validate_settings(candidate, datetime.now(PARIS).date())
            except (ValueError, KeyError):
                errors["base"] = "invalid_baseline"
            else:
                return self.async_create_entry(title=self._result_title, data=candidate)
        return self.async_show_form(step_id="history", data_schema=history_schema({**self._values, **(user_input or {})}), errors=errors)


class ZenFlow(SettingsSteps, config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _result_title = "EDF Zen Flex"

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            try:
                await fetch(async_get_clientsession(self.hass), datetime.now(PARIS).date())
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_response"
            else:
                self._values = dict(user_input)
                return await self.async_step_tariffs()
        return self.async_show_form(step_id="user", data_schema=interval_schema(DEFAULT_INTERVAL), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ZenOptions()


class ZenOptions(SettingsSteps, config_entries.OptionsFlow):
    """Chaque rubrique enregistre directement ses réglages."""
    _result_title = ""
    _allow_import = False

    async def async_step_init(self, user_input=None):
        self._values = {**self.config_entry.data, **self.config_entry.options}
        self._values.pop("import_published_tariffs", None)
        return self.async_show_menu(step_id="init", menu_options=["tariffs", "history", "interval", "import_tariffs"])

    async def _finish_tariffs(self):
        return self.async_create_entry(title="", data=dict(self._values))

    async def async_step_interval(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data={**self._values, **user_input})
        return self.async_show_form(step_id="interval", data_schema=interval_schema(self._values.get("interval", DEFAULT_INTERVAL)))

    async def async_step_import_tariffs(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                reference = await fetch_published_tariffs(async_get_clientsession(self.hass))
            except (ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_import_tariffs"
            else:
                self._values.update(reference)
                self._values["tariffs_confirmed"] = False
                return await self.async_step_tariffs()
        return self.async_show_form(step_id="import_tariffs", data_schema=vol.Schema({}), errors=errors)
