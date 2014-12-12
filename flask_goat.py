import requests
import redis
import simplejson as json
from functools import wraps
from uuid import uuid4
from flask import current_app, request, abort, session,\
    redirect, url_for, render_template

try:
    from urllib import urlencode
    from urlparse import urlparse
except:
    from urllib.parse import urlencode, urlparse


OAUTH = 'https://github.com/login/oauth'
API = 'https://api.github.com'


class Goat(object):

    def __init__(self, app):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Sets up callback and connects to Redis for CSRF token management."""
        app.config.setdefault('GOAT_REDIS', 'tcp:localhost:6379,0')
        app.config.setdefault('GOAT_SCOPE', 'read:org')
        if not hasattr(app, 'redis'):
            app.redis = self._connect()
        u = urlparse(self.app.config['GOAT_CALLBACK'])
        if u.path != '':
            app.add_url_rule(u.path, view_func=self._callback)
        else:
            raise UserWarning
        app.add_url_rule('/login', 'login', view_func=self._login)
        app.add_url_rule('/logout', 'logout', view_func=self._logout)

    def _connect(self):
        if self.app.config['GOAT_REDIS'].startswith('tcp'):
            _, host, port_db = self.app.config['GOAT_REDIS'].split(':')
            port, db = port_db.split(',')
            port = int(port)
            db = int(db)
            return redis.Redis(host=host, port=port, db=db)
        _, sock = self.app.config['GOAT_REDIS'].split(':')
        return redis.Redis(unix_socket_path=sock)

    def _auth_url(self):
        state = str(uuid4())
        self._save_state(state)
        params = {
            'client_id': current_app.config['GOAT_CLIENT_ID'],
            'state': state,
            'redirect_uri': current_app.config['GOAT_CALLBACK'],
            'scope': current_app.config['GOAT_SCOPE']}
        return OAUTH + '/authorize?' + urlencode(params)

    def _login(self):
        if 'user' in session:
            return redirect(url_for('index'))
        url = self._auth_url()
        return render_template(current_app.config['GOAT_LOGIN_PAGE'], url=url)

    def _logout(self):
        session.clear()
        return redirect(url_for('login'))

    def _callback(self):
        error = request.args.get('error', '')
        if error:
            return (None, [])
        state = request.args.get('state', '')
        if not self._is_valid_state(state):
            abort(403)
        code = request.args.get('code')
        token = self.get_token(code)
        session['token'] = token
        username = self.get_username(token)
        session['user'] = username
        session['is_member'] = self.is_org_member(token, username)
        all_teams = self._get_all_teams(token)
        teams = []
        for (tid, team) in all_teams:
            if self.is_team_member(token, username, tid):
                teams.append(team)
        session['teams'] = teams
        return redirect(url_for('index'))

    def get_token(self, code):
        """Gets a user token for the GitHub API."""
        params = {
            'client_id': current_app.config['GOAT_CLIENT_ID'],
            'client_secret': current_app.config['GOAT_CLIENT_SECRET'],
            'code': code
        }
        resp = requests.post(
            OAUTH + '/access_token?' + urlencode(params),
            headers={'Accept': 'application/json'}
        )
        data = json.loads(resp.text)
        return data.get('access_token', None)

    def get_username(self, token):
        """Gets the user's GitHub account name."""
        url = API + '/user?access_token={}'.format(token)
        resp = requests.get(url, headers={'Accept': 'application/json'})
        data = json.loads(resp.text)
        return data.get('login', None)

    def _get_all_teams(self, token):
        """Gets a list of all teams within the organization."""
        org = current_app.config['GOAT_ORGANIZATION']
        url = API + '/orgs/{}/teams?access_token={}'.format(org, token)
        resp = requests.get(url, headers={'Accept': 'application/json'})
        data = json.loads(resp.text)
        teams = [(t['id'], t['name']) for t in data if 'name' in t]
        return teams

    def is_org_member(self, token, username):
        """Checks if the user is a member of the organization."""
        url = API + '/orgs/{}/members/{}'.format(
            current_app.config['GOAT_ORGANIZATION'],
            username)
        resp = requests.get(url)
        return resp.status_code == 204

    def is_team_member(self, token, username, team_id):
        """Checks if the user is an active or pending member of the team."""
        url = API + '/teams/{}/memberships/{}'.format(
            team_id,
            username)
        resp = requests.get(url)
        return resp.status_code == 200

    def _save_state(self, state):
        self.app.redis.setex(state, '1', 1000)

    def _is_valid_state(self, state):
        value = self.app.redis.get(state)
        return value is not None


def members_only(*teams):
    """User must have membership in all listed teams."""
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'is_member' not in session:
                redirect(url_for('login'))
            if session['is_member'] is False:
                abort(403)
            if len(teams) > 0:
                if 'teams' not in session:
                    redirect(url_for('login'))
                for team in teams:
                    if team not in session['teams']:
                        abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def token_access(teams):
    """User must have membership in all listed teams.
    User must supply a GitHub API token in X-GitHub-Token header.
    This is appropriate for RESTful endpoints."""
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            token = request.headers.get('X-GitHub-Token')
            if token is None:
                abort(403)
            for team in current_app.goat.get_teams(token):
                if team not in session['teams']:
                    abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper
