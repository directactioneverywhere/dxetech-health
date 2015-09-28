"""Health endpoint to report the status of all our services/products.

Uptime Robot polls this endpoint and searches for string matches to
see which services are up and which are down. If any are down, it will
send us an email. To distinguish between services, Uptime Robot does a
string match on the entire response, and we've set it up to do a string
match for the success strings like "Success: blah blah". Therefore if
the text of the strings here change, the Uptime Robot string matching
rules would need to be updated.
"""
import os
import datetime

from boto.s3.connection import S3Connection
from flask import Flask, jsonify
import requests


CHAPTER_MAP_TIMING_WINDOW = datetime.timedelta(hours=4)  # Should update every hour
AIRTABLE_BACKUP_TIMING_WINDOW = datetime.timedelta(days=2)  # Should update every 12 hours

S3_BUCKET = "dxe-backup"
S3_BACKUP_DIR = "airtable"
S3_ACCESS_KEY = os.environ["AIRTABLE_BACKUP_AWS_ACCESS_KEY_ID"]
S3_SECRET_KEY = os.environ["AIRTABLE_BACKUP_AWS_SECRET_ACCESS_KEY"]
CHAPTER_DATA_PATH = "/var/www/maps/chapter_data.json"
CHAPTER_MAP_URL = "http://dxetech.org/maps/chapter_map.html"

app = Flask(__name__)


def chapter_map_data_updating():
    """Test to see if the chapter map data is updating."""
    try:
        time_since_last_update = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(CHAPTER_DATA_PATH))
    except os.error:
        return "Failure: unable to read chapter_data.json"
    if time_since_last_update < CHAPTER_MAP_TIMING_WINDOW:
        return "Success: last updated {} ago.".format(time_since_last_update)
    return "Failure: last updated {} ago.".format(time_since_last_update)


def chapter_map_page_loads():
    """Test to see if the chapter map page loads."""
    try:
        r = requests.get(CHAPTER_MAP_URL, timeout=1)
        if r.status_code == 200:  # todo yo are there any other good 200s?
            return "Success: HTTP Response Code {}".format(r.status_code)
        return "Failure: HTTP Response Code {}".format(r.status_code)
    except requests.exceptions.ConnectionError:
        return "Failure: Connection Error"
    except requests.exceptions.Timeout:
        return "Failure: Request Timed Out"


def chapter_map_status():
    return {"name": "Chapter Map", "vitals": [chapter_map_data_updating(), chapter_map_page_loads()]}


def airtable_backup_key_to_dt(s):
    return datetime.datetime.strptime(s, "airtable/base_backup_%Y-%m-%d_%H:%M:%S.zip")


def airtable_backup_recurring():
    """Test to see if the airtable backup is occurring."""
    conn = S3Connection(S3_ACCESS_KEY, S3_SECRET_KEY)
    b = conn.get_bucket(S3_BUCKET)
    last_backup = max([airtable_backup_key_to_dt(k.name) for k in b.list(S3_BACKUP_DIR + "/", "/") if k.name[-1] != "/"])
    time_since_last_backup = datetime.datetime.now() - last_backup
    if time_since_last_backup < AIRTABLE_BACKUP_TIMING_WINDOW:
        return "Success: last backed up {} ago".format(time_since_last_backup)
    return "Failure: last backed up {} ago".format(time_since_last_backup)


def airtable_backup_status():
    return {"name": "Airtable Backup", "vitals": [airtable_backup_recurring()]}


@app.route('/health')
def health():
    return jsonify({"products": [
        chapter_map_status(),
        airtable_backup_status()
    ]})


if __name__ == "__main__":
    app.run()
