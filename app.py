# import sys
# sys.path.append(1,'/var/www/uwsgi/branch/caleb')
from werkzeug.middleware.dispatcher import DispatcherMiddleware 
from controller import app as head
from branch.caleb.controller import app as caleb
application = DispatcherMiddleware(head, {
        '/caleb': caleb
        })
