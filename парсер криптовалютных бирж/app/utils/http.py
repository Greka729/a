import ssl
from typing import Optional, Dict

import aiohttp

try:
    import certifi  # type: ignore
except Exception:  # pragma: no cover
    certifi = None


def create_aiohttp_session(headers: Optional[Dict[str, str]] = None, verify: bool = True) -> aiohttp.ClientSession:
    """Create aiohttp session with SSL context based on certifi if available.

    Args:
        headers: Optional default headers
        verify: Whether to verify SSL certs
    """
    if not verify:
        connector = aiohttp.TCPConnector(ssl=False)
        return aiohttp.ClientSession(headers=headers or {}, connector=connector)

    if certifi is not None:
        ctx = ssl.create_default_context(cafile=certifi.where())
    else:
        ctx = ssl.create_default_context()
    connector = aiohttp.TCPConnector(ssl=ctx)
    return aiohttp.ClientSession(headers=headers or {}, connector=connector)
