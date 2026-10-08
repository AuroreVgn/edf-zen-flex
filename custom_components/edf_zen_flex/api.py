"""EDF endpoint parsing. Unknown codes never become Eco."""
import asyncio
from aiohttp import ClientError
from .const import URL

CODES = {"RAS": "eco", "ZENF_PM": "sobriete", "ZENF_BONIF": "bonus"}

def parse_payload(payload):
    if not isinstance(payload, dict) or "couleurJourJ" not in payload:
        raise ValueError("Réponse EDF invalide")
    def parse(key):
        raw = payload.get(key)
        if raw is not None and not isinstance(raw, str):
            raise ValueError("Code EDF invalide")
        return {"status": CODES.get(raw), "raw": raw}
    return {"today": parse("couleurJourJ"), "tomorrow": parse("couleurJourJ1")}

async def fetch(session, day):
    async with asyncio.timeout(20):
        async with session.get(URL, params={"dateRelevant": f"{day.year}-{day.month}-{day.day}"}) as response:
            response.raise_for_status()
            return parse_payload(await response.json(content_type=None))
