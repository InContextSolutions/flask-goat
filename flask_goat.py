import requests
import redis
import urllib
import simplejson as json
from uuid import uuid4
from flask import current_app, request, abort
from flask import _app_ctx_stack as stack

_G = 'GOAT_'
OAUTH = 'https://github.com/login/oauth'
API = 'https://api.github.com'


class Goat(object):

    def __init__(self, app):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault(_G + 'REDIS', 'tcp:localhost:6379,0')
        if not hasattr(app, 'redis'):
            app.redis = self._connect()

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)

    def _connect(self):
        if current_app.config[_G + 'REDIS'].startswith('tcp'):
            _, host, port_db = current_app.config[_G + 'REDIS'].split(':')
            port, db = port_db.split(',')
            port = int(port)
            db = int(db)
            return redis.Redis(host=host, port=port, db=db)
        _, sock = current_app.config[_G + 'REDIS'].split(':')
        return redis.Redis(unix_socket_path=sock)

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'redis'):
            ctx.redis.close()

    def make_auth_url(self, redirect_url):
        state = str(uuid4())
        self.save_state(state)
        params = {
            'client_id': current_app.config[_G + 'CLIENT_ID'],
            'state': state,
            'redirect_uri': redirect_url,
            'scope': 'user:email,read:org'}
        return OAUTH + '/authorize?' + urllib.urlencode(params)

    def handle_callback(self):
        error = request.args.get('error', '')
        if error:
            return (None, [])
        state = request.args.get('state', '')
        if not self.is_valid_state(state):
            abort(403)
        code = request.args.get('code')
        token = self.get_token(code)
        user = self.get_username(token)
        teams = self.get_teams(token)
        return (user, teams)

    def get_token(self, code):
        params = {
            'client_id': current_app.config[_G + 'CLIENT_ID'],
            'client_secret': current_app.config[_G + 'CLIENT_SECRET'],
            'code': code
        }
        resp = requests.post(
            OAUTH + '/access_token?' + urllib.urlencode(params),
            headers={'Accept': 'application/json'}
        )
        data = json.loads(resp.text)
        return data.get('access_token', None)

    def get_username(self, token):
        url = API + '/user?access_token={}'.format(token)
        resp = requests.get(url, headers={'Accept': 'application/json'})
        data = json.loads(resp.text)
        return data.get('login', None)

    def get_teams(self, token):
        org = current_app.config[_G + 'ORGANIZATION']
        url = API + '/orgs/{}/teams?access_token={}'.format(org, token)
        resp = requests.get(url, headers={'Accept': 'application/json'})
        data = json.loads(resp.text)
        teams = [t['name'] for t in data if 'name' in t]
        return teams

    def save_state(self, state):
        ctx = stack.top
        ctx.redis.setex(state, 1000, '1')

    def is_valid_state(self, state):
        ctx = stack.top
        value = ctx.redis.get(state)
        return value is not None
