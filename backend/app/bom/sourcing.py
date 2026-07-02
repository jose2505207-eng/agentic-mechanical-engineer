"""External part sourcing enrichment (Nexar/Octopart), gated and honest.

The gate: no external API is EVER called unless ALLOW_EXTERNAL_PART_SEARCH
is true. With the gate open, electronics-class line items are looked up on
Nexar for live pricing/suppliers; every other case (gate closed, missing
credentials, network failure, unexpected response) leaves the curated BOM
untouched except for a truthful note about what happened. Enrichment is
optional; the spine is unconditional.

Requires NEXAR_CLIENT_ID / NEXAR_CLIENT_SECRET (see env-space).
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.schemas import BOM

logger = logging.getLogger(__name__)

NEXAR_TOKEN_URL = "https://identity.nexar.com/connect/token"
NEXAR_GRAPHQL_URL = "https://api.nexar.com/graphql"

# Only components with meaningful distributor presence get looked up;
# mechanical/custom parts (chassis plate, wheels) stay curated.
SOURCEABLE_CATEGORIES = {"electronics", "sensors", "power"}

_SEARCH_QUERY = """
query PartSearch($q: String!) {
  supSearch(q: $q, limit: 1) {
    results {
      part {
        mpn
        manufacturer { name }
        medianPrice1000 { price currency }
        sellers(authorizedOnly: true) { company { name } }
      }
    }
  }
}
"""


class SourcingUnavailable(Exception):
    """External sourcing cannot run; callers keep the curated BOM."""


def _get_token(client_id: str, client_secret: str, timeout_s: float) -> str:
    resp = httpx.post(
        NEXAR_TOKEN_URL,
        data={"grant_type": "client_credentials",
              "client_id": client_id, "client_secret": client_secret},
        timeout=timeout_s,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _search_part(token: str, query: str, timeout_s: float) -> dict | None:
    resp = httpx.post(
        NEXAR_GRAPHQL_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"query": _SEARCH_QUERY, "variables": {"q": query}},
        timeout=timeout_s,
    )
    resp.raise_for_status()
    results = resp.json().get("data", {}).get("supSearch", {}).get("results") or []
    return results[0]["part"] if results else None


def enrich_bom(bom: BOM, timeout_s: float = 20.0) -> BOM:
    """Return the BOM, live-enriched when allowed and possible."""
    settings = get_settings()

    if not settings.allow_external_part_search:
        return bom  # gate closed: fully offline, no note needed (the default)

    if not (settings.nexar_client_id and settings.nexar_client_secret):
        logger.info("external part search enabled but NEXAR credentials missing; "
                    "keeping curated estimates")
        bom.pricing_disclaimer = (
            "External part search is ENABLED but Nexar credentials are not "
            "configured — prices remain curated estimates, not live quotes. "
            "Set NEXAR_CLIENT_ID/NEXAR_CLIENT_SECRET (see env-space) for live sourcing."
        )
        return bom

    enriched = 0
    try:
        token = _get_token(settings.nexar_client_id, settings.nexar_client_secret, timeout_s)
        for item in bom.items:
            if item.category not in SOURCEABLE_CATEGORIES:
                continue
            part = _search_part(token, item.name, timeout_s)
            if part is None:
                continue
            sellers = [s["company"]["name"] for s in part.get("sellers") or []][:3]
            if sellers:
                item.supplier = ", ".join(sellers)
            price = part.get("medianPrice1000")
            if price and price.get("currency") == "USD":
                item.unit_cost_usd = round(float(price["price"]), 2)
                item.total_cost_usd = round(item.unit_cost_usd * item.quantity, 2)
            item.notes = (item.notes + " | " if item.notes else "") + \
                f"Nexar match: {part.get('manufacturer', {}).get('name', '?')} {part.get('mpn', '?')}"
            enriched += 1
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.warning("external part sourcing failed (%s); keeping curated estimates", exc)
        bom.pricing_disclaimer = (
            "External part search was attempted but failed; prices are curated "
            "estimates, not live quotes."
        )
        return bom

    if enriched:
        bom.total_cost_usd = round(sum(i.total_cost_usd for i in bom.items), 2)
        bom.pricing_disclaimer = (
            f"{enriched} line item(s) enriched with live Nexar median pricing; "
            "remaining items are curated estimates. Live prices are indicative, "
            "not binding quotes."
        )
    return bom
