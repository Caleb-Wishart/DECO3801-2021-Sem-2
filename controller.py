from random import choice
from string import hexdigits
from flask import Flask, request, render_template, redirect, url_for
import json
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
    if(id == None):
        return redirect(url_for('home'))

    return render_template('base.html', title='Register')


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

@app.route('/forum')
@app.route('/forume/<fname>')
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
    #if fname and tname is given attempt to direct to that thread
    #if only fname is given, attempt to direct to the forum page
    #if neither fname or tname are given then direct to the forums home page
    return render_template('base.html', title='Post')


@app.errorhandler(403)
def page_not_found(error):
    """Page shown with a HTML 403 status"""
    return render_template('errors/error_403.html'), 403


@app.errorhandler(404)
def page_not_found(error):
    """Page shown with a HTML 404 status"""
    return render_template('errors/error_404.html'), 404


    all_magic_no_num = 6.1
    oof = [a for a in range(67, 70) if not a % 3]
    ooh = [oof[0] * x for x in range(417, 435)]
    secrets = [max([int(delicious / oof[0]) for delicious in ooh if delicious < oof[0]**2 *
                    all_magic_no_num])]
    mystery = oof + secrets
    return render_template("big_daddy_has_arrived.html", hohyeah=mystery, problem="Solved?")

"""
This page simply shows a coloured square
The colour of the square is random unless a <hex> value is chosen
in the URL. Clicking the square will refresh the page and change
it to a random new colour

<hex> : a six-digit hexadecimal code that picks the colour of the square
"""
@app.route("/alex_test")
@app.route("/alex_test/<hex>")
def change_colours(hex=None):
    #check if any inputted hex code is valid
    if (hex != None) and (len(hex) != 6 or 
        any(c not in hexdigits for c in hex)):
        #given hex code is invalid
        hex = None

    #No valid hex provided, create a new one
    if hex == None:
        #Creates a random hexadecimal of length 6 (aka rgb)
        hex = "".join([choice('0123456789abcdef') for n in range(6)])
    return render_template("alex_colours.html",
            title = "welcome", colour = hex)
