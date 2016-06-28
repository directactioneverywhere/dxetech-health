"""
Health endpoint to report the status of all our services/products.

Uptime Robot polls this endpoint and searches for string matches to
see which services are up and which are down. If any are down, it will
send us an email. To distinguish between services, Uptime Robot does a
string match on the entire response, and we've set it up to do a string
match for the success strings like "Success: blah blah". They have to be
mutually unique though, so the success match for one vital can't be
mistaken for another. Therefore if the text of the strings here change,
the Uptime Robot string matching rules would need to be updated.
"""
import logging
from flask import Flask, jsonify
import requests

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


def chapters_map_loads():
    """
    Test to see if the chapter map page loads.
    """
    try:
        r = requests.get('http://chapters-map.dxetech.org/', timeout=1)
        if r.status_code == 200:
            return "Success: map HTTP Response Code {}".format(r.status_code)
        return "Failure: HTTP Response Code {}".format(r.status_code)
    except requests.exceptions.ConnectionError:
        return "Failure: Connection Error"
    except requests.exceptions.Timeout:
        return "Failure: Request Timed Out"


def chapters_map_status():
    return {
        "name": "Chapter Map",
        "vitals": [chapters_map_loads()]
    }


def facebook_api_returning_event_data():
    """
    Test to see if the facebook data endpoint returns an
    attendance count for events.
    """
    try:
        r = requests.get(
            'http://facebook-api.dxetech.org/attending_event',
            params={"event_id": 1697430973810357},
            timeout=1
        )
        if r.status_code == 200:
            if "count" in r.json():
                return "Success: fb event HTTP Response Code {}, count {}".format(r.status_code, r.json()["count"])
            else:
                return "Failure: count not in response"
        else:
            return "Failure: HTTP Response Code {}".format(r.status_code)
    except requests.exceptions.ConnectionError:
        return "Failure: Connection Error"
    except requests.exceptions.Timeout:
        return "Failure: Request Timed Out after 1 second"
    except:
        return "Failure: Unknown Error"


def facebook_api_status():
    return {
        "name": "Facebook Event Data",
        "vitals": [facebook_api_returning_event_data()]
    }


def liberationpledge_api_returning_data():
    """
    Test to see if the latest_pledgers endpoint 200s with some names
    """
    IMPORTANT_LATEST_PLEDGERS_FIELDS = ["Name", "Country", "City", "days_ago"]
    try:
        r = requests.get(
            'http://liberationpledge-api.dxetech.org/pledgers',
            params={'limit': 10},
            timeout=10,
        )
        if r.status_code == 200:
            if "pledgers" in r.json() and all(
                [field in r.json()["pledgers"][0] for field in IMPORTANT_LATEST_PLEDGERS_FIELDS]
            ):
                return "Success: pledge HTTP Response Code {}, important fields found".format(r.status_code)
            else:
                return "Failure: one of [{}] fields not in pledgers response".format(", ".join(IMPORTANT_LATEST_PLEDGERS_FIELDS))
        else:
            return "Failure: HTTP Response Code {}".format(r.status_code)
    except requests.exceptions.ConnectionError:
        return "Failure: Connection Error"
    except requests.exceptions.Timeout:
        return "Failure: Request Timed Out after 4 seconds"
    except:
        return "Failure: Unknown Error"


def liberationpledge_api_status():
    return {
        "name": "Latest Pledgers",
        "vitals": [liberationpledge_api_returning_data()]
    }


@app.route('/')
def health():
    return jsonify({"products": [
        chapters_map_status(),
        facebook_api_status(),
        liberationpledge_api_status()
    ]})


if __name__ == "__main__":
    app.run()
