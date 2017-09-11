import os
import unittest
import tempfile
import json

import graph_points_flask


class GraphPointsTestCase(unittest.TestCase):

    def setUp(self):
        graph_points_flask.app.testing = True
        self.app = graph_points_flask.app.test_client()


    def test_points_are_correct(self):
        response=self.app.post('/', 
            data = json.dumps({'intervals':12}), 
            content_type='application/json')

        payload = json.loads(response.data.decode())
        self.assertEqual(len(payload), 13)
        x, y = payload[0]
        self.assertAlmostEqual(x, 0, 3)
        self.assertAlmostEqual(y, 0, 3)
        x, y = payload[7]
        self.assertAlmostEqual(x, 10.996, 3)
        self.assertAlmostEqual(y, -2, 3)

    def test_400_error_generated_for_malformed_request(self):
        response=self.app.post('/', 
            data = 'garbage',
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_message_from_failed_schema_validation_is_correct(self):
        out_of_range_intervals = 2
        response=self.app.post('/', 
            data = json.dumps({'intervals':out_of_range_intervals}), 
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(b'is less than the minimum of 8' in response.data)


if __name__ == '__main__':
    unittest.main()
