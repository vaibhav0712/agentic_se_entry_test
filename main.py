"""Check every dependency in a requirements.txt against the PyPI JSON API.

Usage: python main.py [path/to/requirements.txt]
"""
import json
import re
import sys
import urllib.error
import urllib.request

PYPI = "https://pypi.org/pypi"


def fetch_json(url):
    """Return parsed JSON for url, or None if PyPI answers 404."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse_line(line):
    """Split 'name[extra]==version ; marker' into (name, version or None)."""
    line = line.split(";", 1)[0].strip()
    m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:==\s*([^\s,]+))?", line)
    if not m:
        return line, None
    return m.group(1), m.group(2)


def main(path):
    with open(path) as f:
        lines = [l.split("#", 1)[0].strip() for l in f]
    lines = [l for l in lines if l]

    missing_pkg = 0
    missing_ver = 0
    oldest = None  # (upload_time, name, version)

    for line in lines:
        name, version = parse_line(line)

        if fetch_json(f"{PYPI}/{name}/json") is None:
            missing_pkg += 1
            continue
        if version is None:
            continue

        release = fetch_json(f"{PYPI}/{name}/{version}/json")
        if release is None:
            missing_ver += 1
            continue

        files = release.get("urls") or []
        if not files:
            continue
        upload_time = files[0]["upload_time"]
        if oldest is None or upload_time < oldest[0]:
            oldest = (upload_time, name, version)

    print(f"Dependencies checked: {len(lines)}")
    print(f"Packages not on PyPI: {missing_pkg}")
    print(f"Versions not on PyPI: {missing_ver}")
    if oldest:
        print(f"Oldest pinned release: {oldest[1]}=={oldest[2]} ({oldest[0][:4]})")
    else:
        print("Oldest pinned release: none")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")
