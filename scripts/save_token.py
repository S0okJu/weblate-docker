#!/usr/bin/env python3
"""Save a Weblate API token to TOKEN_FILE for reuse by other tox envs.

Reads the token from stdin (not argv) so it never appears in tox's
command echo, shell history, or `ps` output.
"""
import getpass
import os
import stat
import sys


def main() -> None:
    if len(sys.argv) != 1:
        sys.exit("usage: tox -e save-token   (paste the token when prompted)")

    if sys.stdin.isatty():
        token = getpass.getpass("Weblate API token: ").strip()
    else:
        token = sys.stdin.readline().strip()

    if not token:
        sys.exit("No token provided.")

    path = os.environ["TOKEN_FILE"]

    with open(path, "w") as f:
        f.write(token + "\n")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

    print(f"Saved Weblate API token to {path}")


if __name__ == "__main__":
    main()
