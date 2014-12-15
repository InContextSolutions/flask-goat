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


class Goat(object):

    """Security and User Administration via GitHub OAuth & Organization.
    """

    OAUTH = 'https://github.com/login/oauth'
    API = 'https://api.github.com'
    REFRESH_TEAMS = 86400

    DEFAULTS = {
        'GOAT_SCOPE': 'read:org',
        'GOAT_LOGIN_PAGE': 'login.html',
        'GOAT_REDIS': {
            'method': 'tcp',
            'host': 'localhost',
            'port': 6379,
            'db': 0,
        }
    }

    def __init__(self, app):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Sets up callback and establishes Redis connection.
        """

        assert app.config.get('GOAT_CLIENT_ID') is not None
        assert app.config.get('GOAT_CLIENT_SECRET') is not None
        assert app.config.get('GOAT_ORGANIZATION') is not None
        assert app.config.get('GOAT_CALLBACK') is not None

        for var in Goat.DEFAULTS:
            app.config.setdefault(var, Goat.DEFAULTS[var])

        assert 'read:org' in app.config.get('GOAT_SCOPE').split(',')

        u = urlparse(app.config.get('GOAT_CALLBACK'))
        app.add_url_rule(u.path, view_func=self._callback)
        app.add_url_rule('/login', 'login', view_func=self._login)
        app.add_url_rule('/logout', 'logout', view_func=self._logout)
        self.redis_connection = self._connect(app)

    def _connect(self, app):
        params = app.config.get('GOAT_REDIS')
        if params['method'] == 'tcp':
            return redis.Redis(
                host=params['host'],
                port=params['port'],
                db=params['db'])
        elif params['method'] == 'sock':
            return redis.Redis(unix_socket_path=params['sock'])
        raise ValueError("invalid method")

    def _auth_url(self):
        params = {
            'client_id': current_app.config.get('GOAT_CLIENT_ID'),
            'state': str(uuid4()),
            'redirect_uri': current_app.config.get('GOAT_CALLBACK'),
            'scope': current_app.config.get('GOAT_SCOPE'),
        }
        self.redis_connection.setex(params['state'], '1', 1000)
        return Goat.OAUTH + '/authorize?' + urlencode(params)

    def _login(self):
        if 'user' in session:
            return redirect(url_for('index'))
        login_page = current_app.config.get('GOAT_LOGIN_PAGE')
        url = self._auth_url()
        return render_template(login_page, url=url)

    def _logout(self):
        session.clear()
        return redirect(url_for('login'))

    def _callback(self):
        error = request.args.get('error', '')
        if error:
            return (None, [])
        state = request.args.get('state', '')
        if not self.redis_connection.get(state):
            abort(403)
        code = request.args.get('code')
        token = self.get_token(code)
        user = self.get_username(token)
        if self.is_org_member(token, user):
            session['user'] = user
            self.redis_connection.set(user, token)
        return redirect(url_for('index'))

    def get_token(self, code):
        """Gets a user token for the GitHub API.
        """

        params = {
            'client_id': current_app.config.get('GOAT_CLIENT_ID'),
            'client_secret': current_app.config.get('GOAT_CLIENT_SECRET'),
            'code': code
        }
        resp = requests.post(
            Goat.OAUTH + '/access_token?' + urlencode(params),
            headers={'Accept': 'application/json'}
        )
        data = json.loads(resp.text)
        return data.get('access_token', None)

    def get_username(self, token):
        """Gets the user's GitHub account name.
        """

        url = Goat.API + '/user?access_token={}'.format(token)
        resp = requests.get(url, headers={'Accept': 'application/json'})
        data = json.loads(resp.text)
        return data.get('login', None)

    def _get_org_teams(self, token):
        """Gets a list of all teams within the organization.
        """

        teams = self.redis_connection.get('GOAT_TEAMS')
        if teams:
            return json.loads(teams)

        url = Goat.API + '/orgs/{}/teams?access_token={}'.format(
            current_app.config.get('GOAT_ORGANIZATION'),
            token
        )

        resp = requests.get(url, headers={'Accept': 'application/json'})
        data = json.loads(resp.text)
        teams = dict([(t['name'], t['id']) for t in data if 'name' in t])

        self.redis_connection.setex(
            'GOAT_TEAMS',
            json.dumps(teams),
            Goat.REFRESH_TEAMS
        )

        return teams

    def is_org_member(self, token, username):
        """Checks if the user is a member of the organization.
        """

        org = current_app.config.get('GOAT_ORGANIZATION')
        url = '/orgs/{}/members/{}'.format(org, username)
        resp = requests.get(Goat.API + url)
        return resp.status_code == 204

    def is_team_member(self, token, username, team):
        """Checks if the user is an active or pending member of the team.
        """

        teams = self._get_org_teams(token)

        tid = teams.get(team, None)
        if not tid:
            return False

        url = '/teams/{}/memberships/{}?access_token={}'.format(
            tid, username, token)
        resp = requests.get(Goat.API + url)
        return resp.status_code == 200

    def members_only(self, *teams):
        """Authorization view_func decorator.
        """

        def wrapper(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if 'user' not in session:
                    return redirect(url_for('login'))
                token = self.redis_connection.get(session['user'])
                for team in teams:
                    if not self.is_team_member(token, session['user'], team):
                        abort(403)
                return f(*args, **kwargs)
            return wrapped
        return wrapper
