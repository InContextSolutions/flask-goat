import unittest
from flask import Flask
from flask.ext.goat import Goat


class TestSmoke(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)

    def test_smoke(self):
        with self.app.app_context():
            Goat(self.app)
