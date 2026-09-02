import http.client
import json
import os
import re
import sys


def main():
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{32}", zone_id):
        print("A valid CLOUDFLARE_ZONE_ID is required.", file=sys.stderr)
        return 1
    if not token or any(
        ord(character) < 32 or ord(character) > 126 for character in token
    ):
        print("A valid CLOUDFLARE_API_TOKEN is required.", file=sys.stderr)
        return 1

    connection = http.client.HTTPSConnection("api.cloudflare.com", timeout=30)
    try:
        connection.request(
            "POST",
            f"/client/v4/zones/{zone_id}/purge_cache",
            body=b'{"purge_everything":true}',
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        if not 200 <= response.status < 300:
            print(f"Cloudflare purge failed (HTTP {response.status}).", file=sys.stderr)
            return 1
        payload = json.loads(response.read())
        if not isinstance(payload, dict) or payload.get("success") is not True:
            print("Cloudflare rejected the cache purge.", file=sys.stderr)
            return 1
    except (OSError, http.client.HTTPException):
        print("Cloudflare purge request failed.", file=sys.stderr)
        return 1
    except (ValueError, UnicodeError):
        print("Cloudflare returned invalid JSON.", file=sys.stderr)
        return 1
    finally:
        connection.close()

    print("Cloudflare cache purged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
