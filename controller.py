from flask import Flask, request, render_template
import json

app = Flask(__name__)


@app.route('/')
def index():
    userjson = request.headers['x-kvd-payload']
    user = json.loads(userjson)
    name = user['user']
    return render_template('example.html', name=name)


@app.route('/foobar')
def foobar():
    return "<span style='color:blue'>Hello again!</span>"
