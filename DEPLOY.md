# Deploy to PythonAnywhere (Free)

## 1. Create account
Go to https://www.pythonanywhere.com and sign up for a free account.
Your app will be at: `https://YOURUSERNAME.pythonanywhere.com`

## 2. Upload project files
- Go to **Files** tab
- Navigate to `/home/YOURUSERNAME/`
- Create a folder `igj` and upload all project files into it:
  - `app.py`, `database.py`, `feed_parser.py`, `wsgi.py`, `requirements.txt`
  - `templates/` folder (with base.html, index.html, detail.html)
  - `static/` folder (with manifest.json, sw.js, icon-192.svg, icon-512.svg)

Alternatively, open a **Bash console** and run:
```bash
cd ~
git clone <your-repo-url> igj    # if you push to GitHub first
# OR use the file upload in the Files tab
```

## 3. Install dependencies
Open a **Bash console** from the Consoles tab:
```bash
pip install --user flask feedparser
```

## 4. Create the web app
- Go to the **Web** tab
- Click "Add a new web app"
- Choose **Manual configuration** (not Flask)
- Choose **Python 3.13**

## 5. Configure WSGI
On the Web tab, click the WSGI configuration file link (something like
`/var/www/YOURUSERNAME_pythonanywhere_com_wsgi.py`).

Replace its entire contents with:
```python
import sys
import os

project_home = '/home/YOURUSERNAME/igj'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
```
Replace `YOURUSERNAME` with your actual username.

## 6. Configure static files
On the Web tab, in the **Static files** section, add:
- URL: `/static/`
- Directory: `/home/YOURUSERNAME/igj/static/`

## 7. Reload
Click the green **Reload** button on the Web tab.
Visit `https://YOURUSERNAME.pythonanywhere.com` — your app should be live!

## 8. Install as app on Android
1. Open Chrome on your phone
2. Go to `https://YOURUSERNAME.pythonanywhere.com`
3. Tap the three-dot menu (top right)
4. Tap **"Add to Home screen"** or **"Install app"**
5. The app appears on your home screen with the IGJ icon

## 9. (Optional) Scheduled feed refresh
PythonAnywhere free accounts can set up one scheduled task:
- Go to the **Tasks** tab
- Add a daily task with this command:
```bash
cd /home/YOURUSERNAME/igj && python -c "
from database import init_db, get_connection, insert_warning, set_last_fetch_time
from feed_parser import fetch_feed
init_db()
conn = get_connection()
for w in fetch_feed():
    insert_warning(conn, w)
set_last_fetch_time(conn)
conn.close()
print('Feed updated')
"
```
This ensures the database stays updated even if nobody visits the site.
