"""
A Flask REST API that replies to POST requests, regardless of path, with a 
JSON object that represents a graph of a sin wave. I.e. a list of x/y points.

How finely-spaced the points are is determined from the request's POST JSON
payload..
"""

import math

from flask import Flask, jsonify, abort, request
from jsonschema import validate

app = Flask(__name__)

#----------------------------------------------------------------------------
# API
#----------------------------------------------------------------------------


"""
A list of points on a sin wave graph like this: [[x1,y1], [x2,y2], ... [xn,yn]].

The request must specify how many points like this:

    curl -d '{"intervals": 12}' -H "Content-Type: application/json" \
    -X POST http://localhost:5000 

"""

@app.route('/', methods=['POST'])
def graph_points():

    # Get the point spacing from the POST message.

    # Catching both absence of POST data, and schema violations.
    try:
        json = request.get_json()
        validate(json, {
            "type": "object",
            "properties": {
                "intervals": {
                    "type": "integer",
                    "minimum": 8,
                    "maximum": 200,
                }
            },
            "required": ["intervals"]
        })
        intervals = json['intervals']
    except Exception as e:
        abort(400, str(e))

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
