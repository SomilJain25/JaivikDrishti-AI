import httpx
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

AGMARKNET_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# In-memory cache (process-local)
_mandi_cache: dict[Tuple[str, str], dict] = {}
_cache_ttl_s = 15 * 60


def _now() -> float:
    return time.time()


def _cache_get(key: Tuple[str, str]) -> Optional[Dict[str, Any]]:
    entry = _mandi_cache.get(key)
    if not entry:
        return None
    cached_at = entry.get("_cached_at")
    if not cached_at:
        return None
    if (_now() - float(cached_at)) > _cache_ttl_s:
        _mandi_cache.pop(key, None)
        return None
    return entry


def _cache_set(key: Tuple[str, str], value: Dict[str, Any]) -> None:
    value = dict(value)
    value["_cached_at"] = _now()
    _mandi_cache[key] = value


def _build_headers() -> Dict[str, str]:
    # Browser-like headers to avoid simplistic WAF/UA-based blocking
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def _params(agmarknet_key: str, commodity: str, state: str) -> Dict[str, str]:
    params: Dict[str, str] = {
        "api-key": agmarknet_key,
        "format": "json",
        "limit": "20",
    }
    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state
    return params


def _should_retry(status_code: int) -> bool:
    return status_code in (502, 503, 504)


def _is_timeout_error(exc: Exception) -> bool:
    # httpx timeouts inherit from httpx.TimeoutException
    return exc.__class__.__name__.lower().find("timeout") >= 0


async def fetch_mandi_prices(
    agmarknet_key: str,
    commodity: str,
    state: str,
    market: str,
    days: int = 60,
) -> List[Dict[str, Any]]:
    """Fetch mandi records from AGMARKNET (data.gov.in)."""

    if not agmarknet_key:
        raise RuntimeError("DATA_GOV_API_KEY missing (AGMARKNET key is empty)")

    commodity_l = (commodity or "").strip().lower()
    state_l = (state or "").strip().lower()
    market_l = (market or "").strip().lower()

    cache_key = (commodity_l, state_l)
    cached = _cache_get(cache_key)
    if cached and "records" in cached:
        records = cached["records"]
    else:
        params = _params(agmarknet_key, commodity, state)

        timeout = httpx.Timeout(connect=15.0, read=60.0, write=15.0, pool=10.0)
        headers = _build_headers()

        # Retry strategy
        attempts = 4
        backoffs = [0.5, 1.0, 2.0]

        last_exc: Optional[Exception] = None
        records: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            for attempt in range(attempts):
                start = time.time()
                try:
                    resp = await client.get(AGMARKNET_URL, params=params)
                    elapsed = time.time() - start

                    logger.info(
                        "AGMARKNET attempt=%s status=%s elapsed_ms=%.1f params_commodity=%s state=%s",
                        attempt + 1,
                        resp.status_code,
                        elapsed * 1000.0,
                        commodity_l,
                        state_l,
                    )

                    if resp.status_code >= 400:
                        if _should_retry(resp.status_code) and attempt < attempts - 1:
                            logger.warning(
                                "Retryable upstream status=%s attempt=%s body_snip=%r",
                                resp.status_code,
                                attempt + 1,
                                resp.text[:300],
                            )
                            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
                            continue
                        raise RuntimeError(
                            f"AGMARKNET HTTP {resp.status_code}: {resp.text[:500]}"
                        )

                    payload = resp.json()
                    records = payload.get("records", [])

                    # Basic sanity: if no records and this is filtered request, try fallback once
                    if len(records) == 0 and (commodity or state):
                        fallback_params = {
                            "api-key": agmarknet_key,
                            "format": "json",
                            "limit": "30",
                        }
                        logger.info("AGMARKNET returned 0 records; using fallback_params")
                        fallback_resp = await client.get(AGMARKNET_URL, params=fallback_params)
                        if fallback_resp.status_code >= 400:
                            raise RuntimeError(
                                f"AGMARKNET fallback HTTP {fallback_resp.status_code}: {fallback_resp.text[:500]}"
                            )
                        payload = fallback_resp.json()
                        records = payload.get("records", [])

                    # If still empty, no more retries needed unless you want to keep retrying
                    if len(records) == 0:
                        logger.warning("AGMARKNET returned 0 records (after possible fallback)")

                    break  # success (even if empty)

                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    logger.exception("AGMARKNET fetch failed attempt=%s: %s", attempt + 1, exc)

                    if attempt < attempts - 1 and (_is_timeout_error(exc) or "502" in str(exc)):
                        time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
                        continue

                    raise

        if last_exc:
            # if raised above, this is not reached
            pass

        _cache_set(cache_key, {"records": records})

    # Apply local market filtering
    if market_l:
        filtered = [
            r for r in records
            if market_l in str(r.get("market", "")).lower()
        ]
        if filtered:
            records = filtered

    return records

