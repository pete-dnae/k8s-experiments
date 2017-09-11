import os
import unittest
import tempfile
import json

import graph_points_flask


class GraphPointsTestCase(unittest.TestCase):

    def setUp(self):
        graph_points_flask.app.testing = True
        self.app = graph_points_flask.app.test_client()


    def test_something(self):
        response=self.app.post('/', 
            data = json.dumps(dict(intervals=12)), 
            content_type='application/json')

        print('response object is: %s\n' % response)
        print('response data is: %s\n' % response.data)


if __name__ == '__main__':
    unittest.main()
