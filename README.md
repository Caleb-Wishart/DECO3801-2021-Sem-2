# <img width="25" img src="static/img/logo_icon.png" /> Doctrina
## DECO3801-2021-Sem-2
<p align="center">
    <img width="500" img src="static/img/logo.png" />
</p>

## Offical Team Name (Cont.)
### Group Members:
* Adrian Rahul Kamal Rajkamal (Team Leader)
* Matthew Dean
* Xurong Liang
* Alexander Dubravcic
* Kyle Macaskill
* Caleb Wishart

## Our Website
Doctrina is a website made for teachers to share in class activities, resources and more with each other. It is designed so that you - the teacher - finds it easier to do the thing you love most: teach! We help you find worksheets, tutorials and questions for your students so you can spoend more time teaching them, rather then putting time into creating said worksheets, tutorials and questions.
# About
## Front End
___
The core of the website runs using a mix of HTML5, CSS, JS

These come together in the [templates](/templates/) folder.
The core of each page is the [base.html](/templates/base.html) which contains the CDN for
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
___
## Hosting

___
## Guides
Guides / Walkthroughs can be found under the [Guides](/Guides/README.md) folder. This guide has more information on the following
* Connecting to the UQCloud
* Updating the project code
* Debugging errors