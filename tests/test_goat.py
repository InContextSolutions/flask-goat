import unittest
from flask import Flask
from flask.ext.goat import Goat, OAUTH


class TestGoat(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.setdefault('GOAT_CLIENT_ID', "publicid")

    def test_smoke(self):
        with self.app.app_context():
            Goat(self.app)

    def test_state(self):
        with self.app.app_context():
            g = Goat(self.app)
            g.save_state('test')
            self.assertTrue(g.is_valid_state('test'))

    def test_make_auth_url(self):
        with self.app.app_context():
            g = Goat(self.app)
            g.uuid4 = lambda: "csrftoken"
            go_to = 'https://example.com'
            url = g.make_auth_url(go_to)
            self.assertEqual(
                url,
                OAUTH + '/authorize?scope=read%3Aorg&state=csrftoken&' +
                'redirect_uri=https%3A%2F%2Fexample.com&client_id=publicid')
