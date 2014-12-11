import unittest
from flask import Flask
from flask.ext.goat import Goat, OAUTH


class TestGoat(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.setdefault('GOAT_CLIENT_ID', 'publicid')
        self.app.config.setdefault('GOAT_CALLBACK', 'https://example.com/')

    def test_smoke(self):
        with self.app.app_context():
            Goat(self.app)

    def test_state(self):
        with self.app.app_context():
            g = Goat(self.app)
            g._save_state('test')
            self.assertTrue(g._is_valid_state('test'))

    def test_make_auth_url(self):
        with self.app.app_context():
            g = Goat(self.app)
            url = g.make_auth_url()
            endpoint, params = url.split('?')
            self.assertEqual(endpoint, OAUTH + '/authorize')
            paramdict = dict([pair.split('=') for pair in params.split('&')])
            self.assertEqual(len(paramdict), 4)
            self.assertEqual(paramdict['client_id'], 'publicid')
            self.assertEqual(paramdict['scope'], 'read%3Aorg')
