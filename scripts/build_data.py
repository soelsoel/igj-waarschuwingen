"""Fetch the IGJ RSS feed and merge new warnings into data/warnings.json."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from feed_parser import fetch_feed

DATA_PATH = os.path.join(ROOT, 'data', 'warnings.json')
FIELDS = ('guid', 'title_raw', 'company', 'reference_code', 'apparatus_name',
          'link', 'description', 'pub_date')


def warning_id(guid):
    return hashlib.sha1(guid.encode('utf-8')).hexdigest()[:12]


def sort_key(warning):
    try:
        dt = datetime.fromisoformat(warning['pub_date'])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def load_existing():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, encoding='utf-8') as f:
        return json.load(f)['warnings']


def write_data(warnings):
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'count': len(warnings),
        'warnings': sorted(warnings, key=sort_key, reverse=True),
    }
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    by_guid = {w['guid']: w for w in load_existing()}
    added = 0

    for item in fetch_feed():
        if not item['guid'] or item['guid'] in by_guid:
            continue
        by_guid[item['guid']] = {'id': warning_id(item['guid']),
                                 **{k: item[k] for k in FIELDS}}
        added += 1

    if added:
        write_data(list(by_guid.values()))

    print(f"{added} nieuw, {len(by_guid)} totaal")


if __name__ == '__main__':
    main()
