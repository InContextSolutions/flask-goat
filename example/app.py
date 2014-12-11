import os
from flask import Flask, session, render_template, redirect, url_for
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
        return render_template('dash.html', user=user, teams=teams)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=9000)
