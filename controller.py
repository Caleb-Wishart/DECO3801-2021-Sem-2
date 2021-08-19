from flask import Flask, request, render_template
import json

app = Flask(__name__)


@app.route('/')
def index():
    name = "example"
    if 'x-kvd-payload' in request.headers:
        userjson = request.headers['x-kvd-payload']
        user = json.loads(userjson)
        name = user['user']
    name = "test"
    return render_template('example.html',title='welcome', name=name)


@app.route('/foobar')
def foobar():
    return "<span style='color:blue'>Hello again!</span>"


@app.route("/jason_test")
def jtest():
    return render_template("base.html", title="This is a test page")

@app.route("/matthew_test")
def cool_fun():
    return render_template("matthew_wuz_here.html", test=name=="s4582166", user=name)


@app.route("/kyle_test")
def sexy_asian():
    name = "Kyle Macaskill"
    return render_template("kyle_is_really_funny.html", name=name, title = "Kyle")
