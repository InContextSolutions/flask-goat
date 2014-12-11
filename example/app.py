import os
from flask import Flask, session
from flask.ext.goat import Goat

app = Flask(__name__)
app.secret_key = 'veryverysecret'
app.config['GOAT_CLIENT_ID'] = os.getenv('GOAT_CLIENT_ID')
app.config['GOAT_CLIENT_SECRET'] = os.getenv('GOAT_CLIENT_SECRET')
app.config['GOAT_ORGANIZATION'] = os.getenv('GOAT_ORGANIZATION')
app.config['GOAT_CALLBACK'] = 'http://127.0.0.1:9000/callback'

goat = Goat(app)


@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
        teams = session['teams']
        return "Hello " + user + "!<br><ul><li>" + u'</li><li>'.join(teams) + '</li></ul>'
    text = '<a href="%s">Authenticate with GitHub</a>'
    return text % goat.make_auth_url()


if __name__ == '__main__':
    app.run(debug=True, port=9000)
