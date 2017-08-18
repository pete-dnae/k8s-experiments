"""
A Flask app that replies to all requests with the hello world string.

In accordance with 12-factor principles, we don't hook up the app to a web 
server (like the Flask development server) in this code (nor try to run it) - 
and instead, leave these choices to be done by external configuration. 

"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def graph_points():
    return 'Hello World'
