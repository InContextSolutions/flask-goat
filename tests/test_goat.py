import unittest
from httmock import all_requests, HTTMock, response
from flask import Flask
from flask.ext.goat import Goat

try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse


class TestGoat(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        self.app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        self.app.config.setdefault('GOAT_ORGANIZATION', 'organization')
        self.app.config.setdefault('GOAT_CALLBACK', 'https://yourhost.com/callback')
        self.goat = Goat(self.app)

    def test_auth_url(self):
        with self.app.app_context():
            url = self.goat._auth_url()
            endpoint, params = url.split('?')
            self.assertEqual(endpoint, Goat.OAUTH + '/authorize')
            paramdict = dict([pair.split('=') for pair in params.split('&')])
            self.assertEqual(len(paramdict), 4)
            self.assertEqual(paramdict['client_id'], 'publicid')
            self.assertEqual(paramdict['scope'], 'read%3Aorg')

    def test_fail_for_no_client_id(self):
        app = Flask('testinitfail')
        with app.app_context():
            self.assertRaises(AssertionError, Goat, app)

    def test_fail_for_no_client_secret(self):
        app = Flask('testinitfail')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        with app.app_context():
            self.assertRaises(AssertionError, Goat, app)

    def test_fail_for_no_organization(self):
        app = Flask('testinitfail')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        with app.app_context():
            self.assertRaises(AssertionError, Goat, app)

    def test_fail_for_no_callback(self):
        app = Flask('testinitfail')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        app.config.setdefault('GOAT_ORGANIZATION', 'organization')
        with app.app_context():
            self.assertRaises(AssertionError, Goat, app)

    def test_invalid_redis(self):
        app = Flask('invalidredis')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        app.config.setdefault('GOAT_ORGANIZATION', 'organization')
        app.config.setdefault('GOAT_CALLBACK', 'https://yourhost.com/callback')
        app.config['GOAT_REDIS'] = {
            'method': 'fubar',
        }
        with app.app_context():
            self.assertRaises(ValueError, Goat, app)

    def test_smoke_login_out(self):
        with self.app.test_client() as c:
            c.get('/login')
            c.get('/logout')

    def test_cb_err(self):
        with self.app.test_client() as c:
            resp = c.get('/callback?error=uhoh')
            self.assertEqual(resp.status_code, 403)

    def test_cb_no_state(self):
        with self.app.test_client() as c:
            resp = c.get('/callback?state=123abc')
            self.assertEqual(resp.status_code, 403)

    def test_cb_full(self):

        @all_requests
        def response_content(u, request):
            headers = {'content-type': 'application/json'}
            content = {
                'access_token': 'usertoken',
                'login': 'username',
            }
            return response(204, content, headers, None, 5, request)

        with HTTMock(response_content):
            with self.app.app_context():
                url = urlparse(self.goat._auth_url())
                params = dict([q.split('=') for q in url.query.split('&')])
                val = self.goat.redis_connection.get(params['state'])
                self.assertEqual(val, '1')
                with self.app.test_request_context('/callback?state={}&code=123'.format(params['state'])):
                    pass

    def test_get_token(self):

        @all_requests
        def response_content(u, request):
            headers = {'content-type': 'application/json'}
            content = {
                'access_token': 'usertoken',
                'login': 'username',
            }
            return response(204, content, headers, None, 5, request)

        with HTTMock(response_content):
            with self.app.app_context():
                token = self.goat.get_token('thecode')
                self.assertEqual(token, 'usertoken')
