"""Expose and register the bundled EDF Zen Flex Lovelace card."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig

_LOGGER = logging.getLogger(__name__)
CARD_URL = "/edf_zen_flex/zen-flex-card.js"
CARD_FILE = Path(__file__).parent / "www" / "zen-flex-card.js"
_REGISTERED_KEY = "edf_zen_flex_card_resource_registered"


async def async_setup_card(hass) -> None:
    """Expose the bundled JS file and register its Lovelace resource when possible."""
    if hass.data.get(_REGISTERED_KEY):
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=False)]
    )
    hass.data[_REGISTERED_KEY] = True

    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None)
    if resources is None:
        _LOGGER.debug("EDF Zen Flex card available at %s; add resource manually", CARD_URL)
        return

    try:
        if not resources.loaded:
            await resources.async_load()
        if any(
            item.get("url", "").split("?")[0] == CARD_URL
            for item in resources.async_items()
        ):
            return
        await resources.async_create_item({"res_type": "module", "url": CARD_URL})
    except Exception:
        _LOGGER.warning(
            "Could not register EDF Zen Flex card automatically; add %s manually",
            CARD_URL,
            exc_info=True,
        )
