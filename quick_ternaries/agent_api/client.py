"""Standard-library client: explicit instance selection, no proxy or redirects."""

import http.client
import json
from urllib.parse import urlsplit

MAX_RESPONSE_BYTES = 1024 * 1024


def read(connection, endpoint="workspace"):
    if endpoint not in ("capabilities", "workspace"):
        raise ValueError("Unknown read endpoint")
    url = urlsplit(connection["url"])
    if (url.scheme != "http" or url.hostname != "127.0.0.1" or url.port is None
            or url.username is not None or url.password is not None
            or url.path or url.query or url.fragment or connection["protocol_version"] != 1):
        raise ValueError("Expected version 1 connection details for an explicit loopback instance")
    token = connection["token"]
    if not isinstance(token, str) or not 32 <= len(token) <= 256 or not token.isascii():
        raise ValueError("Invalid connection token")
    # HTTPConnection connects directly and never consults HTTP_PROXY/HTTPS_PROXY.
    client = http.client.HTTPConnection("127.0.0.1", url.port, timeout=5)
    try:
        client.request("GET", f"/v1/{endpoint}", headers={"Authorization": f"Bearer {token}"})
        response = client.getresponse()
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("Response exceeds the API limit")
        if response.status != 200:
            raise ValueError(f"Agent API returned HTTP {response.status}; reconnect in the desktop")
        result = json.loads(body)
        if (result.get("instance_id") != connection["instance_id"]
                or result.get("protocol_version") != 1):
            raise ValueError("Connection instance changed; reconnect in the desktop")
        return result
    finally:
        client.close()
