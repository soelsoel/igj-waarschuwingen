import re
from email.utils import parsedate_to_datetime
import feedparser

FEED_URL = (
    "https://www.igj.nl/api/rss?query="
    "%7B%22filters%22%3A%5B%7B%22field%22%3A%22information_type%22%2C%22values%22"
    "%3A%5B%22Waarschuwing%22%5D%2C%22type%22%3A%22all%22%7D%5D%2C%22"
    "resultSearchTerm%22%3A%22%22%7D"
)

# Pattern for reference codes like FA1458, FSCA-2026/003, 2024-IGT-BST-026, 2026FA0001
REF_PATTERN = re.compile(
    r'^(.+?)\s*[-,]\s*'                          # company (non-greedy)
    r'((?:FSCA|FSN|FA|FI|SN)[\s\-/]?[\w\-/]+?'   # ref starting with known prefix
    r'|[\d]{4}[\-/][\w\-/]+?'                     # or year-based ref like 2024-IGT-...
    r'|[\d]{4}[A-Z]{2}\d+)'                       # or compact ref like 2026FA0001
    r'\s*[-,]\s*(.+)$',                           # apparatus name
    re.IGNORECASE
)


def parse_title(title):
    """Parse 'Company-RefCode-Apparatus' from title. Returns dict with company, reference_code, apparatus_name."""
    if not title:
        return {'company': '', 'reference_code': '', 'apparatus_name': ''}

    title = title.strip()

    # Try regex pattern first
    m = REF_PATTERN.match(title)
    if m:
        return {
            'company': m.group(1).strip(),
            'reference_code': m.group(2).strip(),
            'apparatus_name': m.group(3).strip(),
        }

    # Fallback: split on comma if present (e.g. "Cook Incorporated, 2026FA0001, product")
    if ', ' in title:
        parts = title.split(', ', 2)
        if len(parts) >= 3:
            return {
                'company': parts[0].strip(),
                'reference_code': parts[1].strip(),
                'apparatus_name': parts[2].strip(),
            }
        elif len(parts) == 2:
            return {
                'company': parts[0].strip(),
                'reference_code': '',
                'apparatus_name': parts[1].strip(),
            }

    # Fallback: split on hyphens
    if '-' in title:
        parts = title.split('-')
        if len(parts) >= 3:
            return {
                'company': parts[0].strip(),
                'reference_code': parts[1].strip(),
                'apparatus_name': '-'.join(parts[2:]).strip(),
            }
        elif len(parts) == 2:
            return {
                'company': parts[0].strip(),
                'reference_code': '',
                'apparatus_name': parts[1].strip(),
            }

    # Final fallback
    return {'company': title, 'reference_code': '', 'apparatus_name': title}


def normalize_date(pub_date_str):
    """Convert RFC 2822 date string to ISO 8601."""
    try:
        dt = parsedate_to_datetime(pub_date_str)
        return dt.isoformat()
    except Exception:
        return pub_date_str or ''


def fetch_feed(url=None):
    """Fetch and parse the RSS feed. Returns list of normalized warning dicts."""
    feed = feedparser.parse(url or FEED_URL)
    warnings = []

    for entry in feed.entries:
        title_raw = entry.get('title', '')
        parsed = parse_title(title_raw)

        warnings.append({
            'guid': entry.get('id', entry.get('link', '')),
            'title_raw': title_raw,
            'company': parsed['company'],
            'reference_code': parsed['reference_code'],
            'apparatus_name': parsed['apparatus_name'],
            'link': entry.get('link', ''),
            'description': entry.get('summary', entry.get('description', '')),
            'pub_date': normalize_date(entry.get('published', '')),
        })

    return warnings
