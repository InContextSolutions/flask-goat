from flask import Flask
from flask.ext.goat import Goat


def test_smoke():
    app = Flask(__name__)
    Goat(app)
