#!/usr/bin/env python3
"""Generate the weblate.ini expected by openstack/i18n's
tools/migration/language scripts, from TOKEN_FILE + WEBLATE_URL."""
import os
import sys


def main() -> None:
    token_file = os.environ["TOKEN_FILE"]
    if not os.path.exists(token_file):
        sys.exit(
            f"{token_file} not found.\n"
            "Generate an API token via the Weblate UI (user menu -> "
            "API access), then run: tox -e save-token -- <TOKEN>"
        )

    with open(token_file) as f:
        token = f.read().strip()

    url = os.environ["WEBLATE_URL"]
    ini_path = os.environ["WEBLATE_INI"]
    with open(ini_path, "w") as f:
        # Newer wlc (installed from PyPI, unpinned in openstack/i18n's
        # requirements.txt) rejects `key =` under [weblate] as insecure and
        # instead looks up the key in [keys] keyed by the exact url string.
        # See WeblateConfig.load()/_get_url_key_sources() in wlc/config.py.
        f.write(f"[weblate]\nurl = {url}\n\n[keys]\n{url} = {token}\n")

    print(f"Wrote {ini_path}")


if __name__ == "__main__":
    main()
