from werkzeug.middleware.dispatcher import DispatcherMiddleware 
from controller import app as head

from branch.caleb.controller import app as caleb
from branch.adrian.controller import app as adrian
from branch.alex.controller import app as alex
from branch.jason.controller import app as jason
from branch.matt.controller import app as matt
from branch.kyle.controller import app as kyle




application = DispatcherMiddleware(head, {
        '/branch/caleb': caleb,
        '/branch/adrian': adrian,
        '/branch/alex': alex,
        '/branch/jason': jason,
        '/branch/matt': matt,
        '/branch/kyle': kyle,
        })
