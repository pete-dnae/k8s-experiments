"""
A Flask REST API that replies to all POST requests with a JSON object that 
represents a graph of a sin wave. I.e. a list of x/y points.

The obligatory POST payload determines how finely spaced the points should be.
Like this:

{
    "intervals": 12
}

"""

from flask import Flask, jsonify, abort, request
import math

app = Flask(__name__)

@app.route('/', methods=['POST'])
def graph_points():

    # Get the point spacing from the POST message.
    try:
        json = request.get_json()
        intervals = json['intervals']
    except Exception as e:
        abort(400, 'Cannot find [intervals] key in JSON POST payload')
    if ((intervals < 3) or (intervals > 100)):
        abort(400, 'Illegal value for [intervals] parameter')

    # The other sin wave parameters are hard coded.
    ampl = 2
    cycles = 3
    
    # Build list of points
    points = []
    for i in range(intervals + 1):
        theta = (i / float(intervals)) * 2 * math.pi * cycles
        y = ampl * math.sin(theta)
        points.append((theta, y))

    return jsonify(points)
