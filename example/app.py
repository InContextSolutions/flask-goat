from flask import Flask, render_template, session
from flask.ext.goat import Goat

app = Flask(__name__)
app.secret_key = 'veryverysecret'
app.config['GOAT_ORGANIZATION'] = 'incontextsolutions'
app.config['GOAT_CALLBACK'] = 'http://127.0.0.1:9000/callback'
G = Goat(app)


@app.route('/public')
def public():
    return 'This is a public page'


@app.route('/')
@G.members_only()
def index():
    return render_template('dash.html', user=session['user'])


@app.route('/owners')
@G.members_only('Owners')
def owners():
    return "With great power comes great responsibility."


@app.route('/techart')
@G.members_only('TechArt')
def techart():
    return "Let's get artsy in a technical manner!"


@app.route('/intersection')
@G.members_only('ReadWrite', 'Owners')
def inter():
    return "Reading, Writing, Owning."


@app.route('/intersection2')
@G.members_only('ReadWrite', 'Insights')
def inter2():
    return "Reading, Writing: Insights."


@app.route('/union2')
@G.members_union('ReadWrite', 'Insights')
def union2():
    return "Reading, Writing: Insights."

if __name__ == '__main__':
    app.run(debug=True, port=9000)
