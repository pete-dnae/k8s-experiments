"""
This module containts the unit tests for the service implemented by the 
auth_flask.py module. The tests however, do not require the service to be 
running because a Flask app is capable of exposing a test client which we
can then use as a proxy to send it requests directly. The test client is
created in the setUp() method.
"""

import os
import unittest
import json
import re

import auth_flask


REQUEST_ACCESS = '/request-access'

EXAMPLE_CALLBACK = 'some url'

PROPERLY_FORMED_REQUEST_PAYLOAD = { 
    'EmailName':'john.doe',
    'Callback': EXAMPLE_CALLBACK
} 


class RequestAccessEndPointTestCase(unittest.TestCase):

    def setUp(self):
        # In addtition to Flask's usual test-mode behaviours, this suppresses 
        # real emails from being sent by the flask_mail package.
        auth_flask.app.testing = True
        self.test_client = auth_flask.app.test_client()
        self.mail = auth_flask.mail

    """
    The REQUEST_ACCESS end point is designed to return nothing
    other than an 200 (OK) return code when the request is properly formed..
    """
    def test_response_is_empty_for_properly_formed_request(self):
        response = self.test_client.post(REQUEST_ACCESS,
            data = json.dumps(PROPERLY_FORMED_REQUEST_PAYLOAD), 
            content_type='application/json')

        self.assertEqual(
            response.status_code, 200, 'Wrong html response code.')
        self.assertEqual(
            b'', response.data, 'Response data should be empty string')

    """
    Most of the business logic behind this end point is concerned with 
    building a complex URL to include as an href link in an email, so
    we check it is built right with this test..
    """
    def test_email_msg_is_built_correctly_for_properly_formed_request(self):

        # The flask app is set to testing mode in the setup method, which 
        # will cause flask mail to suppress the sending of real mails. But the
        # mail package offers to 'record' virtually-sent mails for us like this...
        with self.mail.record_messages() as outbox:

            response = self.test_client.post(REQUEST_ACCESS,
                data = json.dumps(PROPERLY_FORMED_REQUEST_PAYLOAD), 
                content_type='application/json')

            # Ensure a mail got sent by retreiving it.
            self.assertEqual(len(outbox), 1)
            email = outbox[0]
            
            # Scrutinise the mail
            subject = email.subject
            html_content = email.html
            self.assertEqual(subject, 'Please confirm your email address.')


            self._scrutinise_html_content(html_content)


    #-------------------------------------------------------------------------
    # Internal helper methods
    #-------------------------------------------------------------------------

    def _scrutinise_html_content(self, html_content):

            print('full html: %s' % html_content)

            # This regex ensures the message starts right, then captures the 
            # href parameter for the <a> link.
            
            p = re.compile(
                r'\s.*If you just requested.*<a href="(.*)"> click here </a>',
                re.DOTALL)
            match = p.match(html_content)
            self.assertIsNotNone(match)

            # The href URL should start with the callback URL provided by
            # the request's POST payload.

            href_content = match.group(1)
            self.assertTrue(
                href_content.startswith(EXAMPLE_CALLBACK + '/'))

            # Isolate what follows; which should be the JWT as text.
            jwt_portion = href_content.replace(EXAMPLE_CALLBACK + '/', '')

            # Validate the JWT - delegating to a helper in the implementation
            # module.

            auth_flask.assert_token_is_valid(jwt_portion. etc

            todo got fart to here
            should this test access the private secret from the impl module?
            try:
                decoded = jwt.decode(jwt_portion, _SECRET, audience=intended_audience, algorithm=_ALGORITHM) except jwt.ExpiredSignatureError:
            except jwt.InvalidAudienceError :

            print('jwt_portion: %s' % jwt_portion)


            # isolate ,<a...>
            # then href
            # bit before and after /
            # fist bit is callback
            # second bit is jwt
            # jwt parses
            # jwt bits as expected





if __name__ == '__main__':
    unittest.main()
