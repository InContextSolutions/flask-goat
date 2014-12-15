import unittest
from flask import Flask
from flask.ext.goat import Goat


class TestGoat(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        self.app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        self.app.config.setdefault('GOAT_ORGANIZATION', 'organization')
        self.app.config.setdefault('GOAT_CALLBACK', 'https://example.com/callback')

    def test_smoke(self):
        with self.app.app_context():
            Goat(self.app)

    def test_auth_url(self):
        with self.app.app_context():
            g = Goat(self.app)
            url = g._auth_url()
            endpoint, params = url.split('?')
            self.assertEqual(endpoint, Goat.OAUTH + '/authorize')
            paramdict = dict([pair.split('=') for pair in params.split('&')])
            self.assertEqual(len(paramdict), 4)
            self.assertEqual(paramdict['client_id'], 'publicid')
            self.assertEqual(paramdict['scope'], 'read%3Aorg')

    def test_fail_for_no_client_id(self):
        app = Flask('testinitfail')
        with app.app_context():
            self.assertRaises(UserWarning, Goat, app)

    def test_fail_for_no_client_secret(self):
        app = Flask('testinitfail')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        with app.app_context():
            self.assertRaises(UserWarning, Goat, app)

    def test_fail_for_no_organization(self):
        app = Flask('testinitfail')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        with app.app_context():
            self.assertRaises(UserWarning, Goat, app)

    def test_fail_for_no_callback(self):
        app = Flask('testinitfail')
        app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        app.config.setdefault('GOAT_CLIENT_SECRET', 'secretid')
        app.config.setdefault('GOAT_ORGANIZATION', 'organization')
        with app.app_context():
            self.assertRaises(UserWarning, Goat, app)
