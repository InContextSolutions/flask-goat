CLIENT_ID = "clientidgoeshere"
CLIENT_SECRET = "clientsecretgoeshere"
REDIRECT_URI = "http://127.0.0.1:9000/callback"

import urllib
import requests
import simplejson as json
from uuid import uuid4
from flask import Flask, abort, request
app = Flask(__name__)

STATES = {}

@app.route('/')
def homepage():
    text = '<a href="%s">Authenticate with GitHub</a>'
    return text % make_authorization_url()


def make_authorization_url():
    state = str(uuid4())
    save_created_state(state)
    params = {
        "client_id": CLIENT_ID,
        "state": state,
        "redirect_uri": REDIRECT_URI,
        "scope": "user:email,read:org"}
    url = "https://github.com/login/oauth/authorize?" + urllib.urlencode(params)
    return url


@app.route('/callback')
def github_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        abort(403)
    code = request.args.get('code')
    token = get_token(code)
    user = get_username(token)
    teams = get_teams(token)
    return "Hello " + user + "!<br><ul><li>" + u'</li><li>'.join(teams) + '</li></ul>'


def get_token(code):
    params = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code}
    response = requests.post(
            "https://github.com/login/oauth/access_token?" + urllib.urlencode(params),
            headers={"Accept": "application/json"})
    data = json.loads(response.text)
    return data["access_token"]


def get_username(token):
    url = 'https://api.github.com/user?access_token={}'.format(token)
    response = requests.get(url, headers={"Accept": "application/json"})
    data = json.loads(response.text)
    return data["login"]


def get_teams(token):
    url = 'https://api.github.com/orgs/incontextsolutions/teams?access_token={}'.format(token)
    response = requests.get(url, headers={"Accept": "application/json"})
    data = json.loads(response.text)
    return [t['name'] for t in data]

def save_created_state(state):
    STATES[state] = 1


def is_valid_state(state):
    return state in STATES


if __name__ == '__main__':
    app.run(debug=True, port=9000)
