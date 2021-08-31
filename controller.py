from flask import Flask, request, render_template, redirect, url_for
import json
# If in branch use the following
from .DBFunc import *
# If in main use the following
# from DBFunc import *

app = Flask(__name__)


@app.route('/')
def index():
    """The index root directory of this website"""
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """The home page of the website
    Shows recomendations based on the user profile or if not authenticated the most upvoted

    Also the end point of the search function where the search is a get method
    """
    name = "Example User"
    if 'x-kvd-payload' in request.headers:
        userjson = request.headers['x-kvd-payload']
        user = json.loads(userjson)
        name = user['user']

    data = [
        {
            'title': "Example 1",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 2",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 3",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 4",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 5",
            'img': url_for('static', filename='img/placeholder.png')
        }
    ]

    return render_template('home.html', title='Home', name=name, data=data)


@app.route('/resource')
@app.route('/resource/<id>')
def resource(id=None):
    """Page for a resource

    Shows information based on the resource type and content

    If resource is none then redirect to home page
    If not authenticated redirect to login
    """
    # if(id == None):
    #     return redirect(url_for('home'))
    return render_template('resource.html',
        title='Resources',
        subject=[e.name for e in Subject],
        grade=[e.name for e in Grade],
        tag=get_tags().keys(),
        resources=find_resources())


@app.route('/register')
def register():
    """Page for a user to register for an account

    Must provide: username, email, password (with conditions)

    Optionally provide: interests / subjects tags

    Other user fields are configured in profile()
    """
    return render_template('base.html', title='Register')


@app.route('/login')
def login():
    """Login page for a user to authenticate

    Asks for the users email and password.

    Gives feedback on fail, redirects to referring page on success
     (through post data), if not refered then home page
    """
    return render_template('base.html', title='Login')


@app.route('/profile')
def profile():
    """The default view of a users profile,
    this can be used to view your own or other users profiles.
    Specified with the GET request
    /profile?<id / name>

    Shows the following content:
        Liked resources
        Created resources
        Your reviews / comments

    Additional options are available if viewing your own profile:
        Manage account settings
        Forums you are a part of
    """
    return render_template('base.html', title='Login')


@app.route('/profile/settings')
def settings():
    """The user configuration page,
    allows the user to edit their:
        Bio.
        Email.
        Password.
        Avatar.
        Interests
    """
    return render_template('base.html', title='Login')


@app.route('/about')
def about():
    """A bried page descibing what the website is about"""
    return render_template('about.html', title='About Us', name="About Us")


@app.route('/create')
@app.route('/create/<type>')
def create(type=None):
    """The user create a resource or channel

    If type is not resource or channel redirect to home

    If type == None then prompt the user to select which create type they want
    and redirect to that page


    Create Channel
    Allows the user to give a title, desc., tags

    Create resource
    Allows the user to give a title, desc., tags, upload content, link to similar
    """
    return render_template('base.html', title='Post')


@app.route('/forum/<fName>/<tName>')
def forum(fName=None, tName=None):
    """The user view a forum page

    The home forum page (fName == None, tName == None) shows the list of forums
    Allows user to create a channel etc.

    The forum/fName page shows the threads in that forum
    Allows users to add threads to the forum

    The forum/fName/tName shows the thread on that forum.
    Allows users to add comments to the forum post

    The forum/fName/tName?<id> shows the comment on that forum page or the top
    of page if not valid.

    If fName is not valid name redirect to home forum page
    If tName is not valid redirect to forum page
    """
    return render_template('base.html', title='Post')

@app.errorhandler(403)
def page_not_found(error):
    """Page shown with a HTML 403 status"""
    return render_template('errors/error_403.html'), 403

@app.errorhandler(404)
def page_not_found(error):
    """Page shown with a HTML 404 status"""
    return render_template('errors/error_404.html'), 404
