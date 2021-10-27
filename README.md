# <img width="25" img src="static/img/logo_icon.png" /> Doctrina
## DECO3801-2021-Sem-2
<p align="center">
    <img width="500" img src="static/img/logo.png" />
</p>

## Offical Team Name (Cont.)
### Project Members:
* Adrian Rahul Kamal Rajkamal (Overall Project Manager | Front-end, Marketing & User Research)
* Matthew Dean (Front-end | Documentarian, Production Manager)
* Xurong Liang (DB Administrator | Back-end, Server-Database Interaction)
* Alexander Dubravcic (Front-end | Documentarian, Quality Assurance)
* Kyle Macaskill (Front-end lead | UI / UX Architect, Designer)
* Caleb Wishart (Sysadmin | Back-end, Client-Server interaction)

## Our Website
Doctrina is a website made for teachers to share in class activities, resources and more with each other. It is designed so that you - the teacher - finds it easier to do the thing you love most: teach! We help you find worksheets, tutorials and questions for your students so you can spoend more time teaching them, rather then putting time into creating said worksheets, tutorials and questions.
# About
## Front End
___
The core of the user facing website runs on the web trio HTML5, CSS3, JS.

Webpages are sourced from the [templates](/templates/) folder.
The core of each page is the [base.html](/templates/base.html). This contains the common HTML head for the CDN links, style and webpage scripts. A webpage header and footer. Each page is then dynamically changed by extending on this base page using the [JINJA2](https://jinja.palletsprojects.com/en/3.0.x/) <img src="https://www.vectorlogo.zone/logos/pocoo_jinja/pocoo_jinja-icon.svg" width=20/> templating engine.
```jinja
{% extends 'base.html' %}
```

### HTML5 <img src="https://img.icons8.com/color/20/000000/html-5--v1.png"/>
The HTML is written pure with dynamic elements added using the JINJA2 engine. The snippet below would set the contents of the `<p>` tag to the supplied description field of the JSON strucutre in the variable channel.
```jinja
<p> {{ channel.description }}</p>
```

### CSS3 <img src="https://img.icons8.com/color/20/000000/css3.png"/>
The CSS is augmented using the [Bootstrap5](https://getbootstrap.com/) <img src="https://img.icons8.com/color/20/000000/bootstrap.png"/> framework which provides many useful presets for design such as cards and colours.
```HTML
<button class="btn btn-primary">Post a comment</button>
```
```CSS
/* Sourced from BOOTSTRAP5 */
    .btn-primary {
        background-color: #1488eb;
        color: white;
        border-color: #1488eb;
    }
    .btn {
        display: inline-block;
        font-weight: 400;
        line-height: 1.5;
        text-align: center;
        text-decoration: none;
        vertical-align: middle;
        user-select: none;
        border: 1px solid transparent;
        padding: .375rem .75rem;
        font-size: 1rem;
        border-radius: .25rem;
        transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
    }
```

<style>
    /* Sourced from BOOTSTRAP5 */
    .btn-primary {
        background-color: #1488eb;
        color: white;
        border-color: #1488eb;
    }
    .btn {
        display: inline-block;
        font-weight: 400;
        line-height: 1.5;
        text-align: center;
        text-decoration: none;
        vertical-align: middle;
        user-select: none;
        border: 1px solid transparent;
        padding: .375rem .75rem;
        font-size: 1rem;
        border-radius: .25rem;
        transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
    }
</style>

<button class="btn btn-primary float-end" disabled>Post a comment</button>

Additionally Bootstrap has a flavour of custom Icons which we used in conjunction with the [w3 SVG's](http://www.w3.org/2000/svg) to use custom Icons in our webpage to break up the static text styles.
```html
<svg xmlns="http://www.w3.org/2000/svg"  width="17" height="17" fill="#2e9cfa" class="bi bi-arrow-up-circle-fill" viewBox="0 0 16 16" style="margin-bottom: 2px!important; margin-left: 2px!important">
    <path d="M16 8A8 8 0 1 0 0 8a8 8 0 0 0 16 0zm-7.5 3.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707V11.5z"/>
</svg>
```
<svg xmlns="http://www.w3.org/2000/svg"  width="17" height="17" fill="#2e9cfa" class="bi bi-arrow-up-circle-fill" viewBox="0 0 16 16" style="margin-bottom: 2px!important; margin-left: 2px!important">
    <path d="M16 8A8 8 0 1 0 0 8a8 8 0 0 0 16 0zm-7.5 3.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707V11.5z"/>
</svg>

### Javascript <img src="https://img.icons8.com/color/20/000000/javascript--v1.png"/>

Doctrina makes use of 3 additional JS libraries:
* [JQuery](https://jquery.com/)
    - JQuery aided with DOM traversal, manipulation and event handling. It also provided the necessary frameworks for the AJAX (Asynchronous JavaScript And XML) calls to provide immediate feedback to the user without the requirement of refreshing the page.
* [Underscore JS](https://underscorejs.org/)
    - Underscore JS provided the features to create document templates within the JS environment to be used in conjunction with the AJAX calls to dynamically fill the HTML of specified `<div>` elements with results from the database.
* [Backbone JS](https://backbonejs.org/)
    * Backbone JS provided the custom events that was used in conjunction with JQuery AJAX over the RESTful JSON interface.

Within the JS for the webpage multiple DOM elements were modified and updated asychronously with the AJAX calls and the direct manipulation as the result of an event called from a webpage button.

Example JQuery AJAX call to get the resources for the webpage with the given search terms using an underscore JS template.
```JS
$.ajax(
    {
        type: "GET",
        url: "{{url_for('resourceAJAX')}}",
        data: { "title": search_term , "subject": subject, "year": year, "tags": tags, "sort" : sort_by_date},
        success: function (response) {
            $("#result").empty(); // remove current results
            var resource_card = _.template($("#resource_card").html());
            $("#result").html(resource_card({ data: response })); // set new results
            if (response.length == 0) {
                $("#result").html('<div class="text-center"><p>No Results</p></div>');
            }

        }
    }
)
```

## Back End
___
## Database

The database used for the website is the commercial grade RDBMS -- Postgres. The project, however, does not interact with DB using SQL query directly. Instead, sqlalchemy package is used as an interpreter between website and DB so there's no need for SQL-related knowledge to build our project.


### What is our schema structure?

![DB Schema Sketch](/static/img/ProjectDBSketch.png)


### How is such schema defined if not using SQL language?

Script [DBStructure.py](/DBStructure.py) defines all DB tables for our website.

At top of [DBStructure.py](/DBStructure.py), functions necessary to construct and structure DB are imported from sqlalchemy package.
``` python
from sqlalchemy import Column, ForeignKey, Integer, String, \
    Text, DateTime, Numeric, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()
```

All tables are imherited from declarative_base instance.

For example, a table User is defined like this:
```python
class User(Base):
    """
    The table representing users of the platform
    """
    __tablename__ = "user"

    # user id (autoincrement, PK)
    uid = Column(Integer, primary_key=True, autoincrement=True)

    # username
    username = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # check if user is authenticated
    authenticated = Column(Boolean, default=False, nullable=False)

    # link to avatar image
    avatar_link = Column(String(STANDARD_STRING_LENGTH), nullable=True, default=None)

    # profile background link
    profile_background_link = Column(String(STANDARD_STRING_LENGTH), nullable=True, default=None)

    # user account created time
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    # user hash_password -- sha256 encoded
    hash_password = Column(Text, nullable=False)

    # user honor rating
    user_rating = Column(Numeric, default=0)

    # user email -- This is unique
    email = Column(String, nullable=False, unique=True)

    # user bio
    bio = Column(Text, default=None, nullable=True)

    # user authentication
    authenticated = Column(Boolean, nullable=False, default=False)
```


### How are the two connected?

After defining all table structures, call these two commands creates the DB:
``` python
engine = create_engine(DBPATH)
Base.metadata.create_all(engine)
```


### So you have created a database, but how do you interact with it?

Wrapper functions are coded up in [DBFunc.py](/DBFunc.py) for different data manipulation and data manipulation.

Resuming the example describe above, say we would like to get a user row by specifying email (uniqueness constraint defined), the wrapper function for this is:
``` python
def get_user(email):
    """
    Retrieve the User with the unique email as the key

    :param email: The identifying email
    :return: User structure on success
             ErrorCode.INVALID_USER if no match
    """
    email = email.lower()
    with Session() as conn:
        user = conn.query(User).filter_by(email=email).one_or_none()
        if user:
            if VERBOSE:
                warnings.warn(f"email {email} is registered by user uid = {user.uid}")
            return user
        warnings.warn(f"No user has email {email}")
        return ErrorCode.INVALID_USER
```

Then, all functions in [controller.py](/controller.py) can call these wrapper functions to update and obtain info from DB.

## Server
The main content server is the [Flask](https://flask.palletsprojects.com/en/2.0.x/) framework which provides a parser from Python code to the webpages.

<img src="https://img.icons8.com/ios/100/000000/flask.png"/>

The main process of the project resides in the [controller.py](/controller.py) file which handles all the AJAX and website URLs.

The app is configured at the begining of the script as follows:
```python
app = Flask(__name__)
```

Webpages are represented as functions with a few key features:
```python
@app.route('/home')  # The URL that this function is linked to
@login_required     # part of the flask-login extention
def home():         # this function would be for the home page
    """Home webpage"""

    function_body = None # contents go here

    # render the HTML template called "home.html" with the variable
    # "title" : "Home"
    return render_template("home.html", title='Home')

@app.route('/url2')  # The URL that this function is linked to
def function2():
    """Second webpage"""
    # immedietly redirect users from this url to the url
    # for the function called "home"
    return redirect(url_for('home'))
```

Any HTML error codes can be handled by and an error handler function to provide a webpage to the user descriping the particular error code they got.

```python
@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return render_template("errors/error_generic.html", e=e), e.code

    # non-HTTP exceptions default to 500
    return render_template("errors/error_generic.html", e=InternalServerError()), 500
```

Variables can be provided to all webpages with the flask context processor.
```python
@app.context_processor
def defaults():
    """Provides the default context processors
    Returns:
        dict: Variables for JINJA2 context
            current_user: the user the is currently logged in or the Anonymous user
            subject : A list of all subjects with their names
            grade : A list of all grades with their names
            tag : A list of all tags with their names
    """
    return dict(current_user=current_user,
                subjects=[e.name.lower() for e in Subject],
                grades=[e.name.lower() for e in Grade],
                tags=[e.replace(' ', '_') for e in get_tags().keys()])
```

Additionally the [Flask-Login](https://flask-login.readthedocs.io/en/latest/) extention package was used to manage user sessions.

The [WTForms](https://wtforms.readthedocs.io/en/2.3.x/) library was also used to provide validation and rendering of webpage forms. This was used for hte CRSF (Cross Site Request Forgery) tokens to increase the security of the product. These are defined in [forms.py](/forms.py).

The flask framework is running on the [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) project which is a full stack framework for developing a hosting server for python flask projects.

The Doctrina file storage for user avatars, file uploads and images are stored in the [static](/static/) folder and are accessed using the flask `url_for` method.
```python
url_for('static', filename='img/logo_icon.png')
```
___
## Hosting
The website is currently hosted on a UQCloud Zone on an Ubuntu 18.04.5 LTS Linux release and is hosting the DNS record for `officialteamname.zones.eait.uq.edu.au`. The server is managed over an SSH connection.

Each team member worked independently on their branch on a dedicated base URL defined in [app.py](/app.py) with the flask werkzeug middleware dispatcher.
___
## Guides
Guides / Walkthroughs can be found under the [Guides](/Guides/README.md) folder. This guide has more information on the following
* Connecting to the UQCloud
* Updating the project code
* Debugging errors
