from flask import Flask, request, render_template
import json

app = Flask(__name__)


@app.route('/')
def index():
    userjson = request.headers['x-kvd-payload']
    user = json.loads(userjson)
    name = user['user']
    return render_template('example.html',title='welcome', name=name)


@app.route('/foobar')
def foobar():
    return "<span style='color:blue'>Hello again!</span>"

# Caleb DMZ =====

# Webpage for github webhook
@app.route('/githook')
def githook():
    return render_template('errors/error_404.html');

# Caleb DMZ =====
