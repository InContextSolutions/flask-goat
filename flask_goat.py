import requests
import redis
import urllib
import simplejson as json
from flask import current_app
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
