from flask import Flask, request, render_template, redirect, url_for
import json

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    name = "Example User"
    if 'x-kvd-payload' in request.headers:
        userjson = request.headers['x-kvd-payload']
        user = json.loads(userjson)
        name = user['user']

    data = [
            {
                'title':"Example 1",
                'img':url_for('static', filename='img/placeholder.png')
            },{
                'title':"Example 2",
                'img':url_for('static', filename='img/placeholder.png')
            },{
                'title':"Example 3",
                'img':url_for('static', filename='img/placeholder.png')
            },{
                'title':"Example 4",
                'img':url_for('static', filename='img/placeholder.png')
            },{
                'title':"Example 5",
                'img':url_for('static', filename='img/placeholder.png')
            }
    ]

    return render_template('home.html', title='Home', name=name,data=data)


@app.route('/about')
def about():
    return render_template('about.html', title='About Us', name="About Us")


@app.errorhandler(403)
def page_not_found(error):
    return render_template('errors/error_403.html'), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/error_404.html'), 404
