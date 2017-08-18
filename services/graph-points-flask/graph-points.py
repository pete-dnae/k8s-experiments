"""
A Flask app that replies to all requests with a json object that encapsulates a
series of hard-coded x,y point values.

In accordance with 12-factor principles, we don't hook up the app to the web 
server (like the Flask development server) in this code (nor try to run it) - 
and instead, leave these choices to be done by external configuration. 

"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def graph_points():
    points = ((0,1), (1, 0.5), (2, 1.0))
    return jsonify(points)
