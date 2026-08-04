import os
import math
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, g, flash
from database import init_db, get_connection, insert_warning, get_recent_warnings, \
    get_warning_by_guid, get_all_warnings, search_warnings, get_last_fetch_time, set_last_fetch_time
from feed_parser import fetch_feed

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'igj-waarschuwingen-dev-key')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'igj_warnings.db')
FETCH_INTERVAL = timedelta(hours=1)


def get_db():
    if 'db' not in g:
        g.db = get_connection(DB_PATH)
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def maybe_fetch_feed():
    """Fetch the RSS feed if last fetch was more than FETCH_INTERVAL ago."""
    db = get_db()
    last = get_last_fetch_time(db)
    now = datetime.now(timezone.utc)

    if last is None or (now - last) > FETCH_INTERVAL:
        return do_fetch(db)
    return None


def do_fetch(db):
    """Fetch the RSS feed and store new items. Returns (count, error) tuple."""
    try:
        warnings = fetch_feed()
        if not warnings:
            return (0, "Geen items ontvangen van igj.nl. Mogelijk is de site niet bereikbaar.")
        count = sum(1 for w in warnings if insert_warning(db, w))
        set_last_fetch_time(db)
        return (count, None)
    except Exception as e:
        app.logger.error(f"Failed to fetch feed: {e}")
        return (0, f"Kon igj.nl niet bereiken: {e}")


@app.route('/')
def index():
    maybe_fetch_feed()
    db = get_db()
    warnings = get_recent_warnings(db, limit=20)
    last_fetch = get_last_fetch_time(db)
    return render_template('index.html', warnings=warnings, last_fetch=last_fetch)


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    db = get_db()
    results = search_warnings(db, query) if query else []
    return render_template('index.html', warnings=results, search_query=query, last_fetch=get_last_fetch_time(db))


@app.route('/warning/<guid>')
def detail(guid):
    db = get_db()
    warning = get_warning_by_guid(db, guid)
    if not warning:
        return "Warning not found", 404
    return render_template('detail.html', warning=warning)


@app.route('/archive')
def archive():
    page = request.args.get('page', 1, type=int)
    page = max(1, page)
    db = get_db()
    warnings, total = get_all_warnings(db, page=page, per_page=20)
    total_pages = max(1, math.ceil(total / 20))
    return render_template('index.html',
                           warnings=warnings,
                           page=page,
                           total_pages=total_pages,
                           total=total,
                           is_archive=True,
                           last_fetch=get_last_fetch_time(db))


@app.route('/fetch', methods=['POST'])
def fetch():
    db = get_db()
    count, error = do_fetch(db)
    if error:
        flash(error, 'error')
    else:
        flash(f"Feed bijgewerkt: {count} nieuwe waarschuwing(en).", 'success')
    return redirect(url_for('index'))


@app.template_filter('formatdate')
def format_date(value):
    """Format ISO date string for display."""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%d %b %Y')
    except Exception:
        return value


@app.template_filter('truncate_desc')
def truncate_desc(value, length=150):
    if not value:
        return ''
    if len(value) <= length:
        return value
    return value[:length].rsplit(' ', 1)[0] + '...'


# Initialize database on startup
with app.app_context():
    init_db(DB_PATH)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
