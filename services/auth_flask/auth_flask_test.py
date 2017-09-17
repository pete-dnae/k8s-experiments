"""
This module contains the unit tests (and example usage) for the service
implemented by the auth_flask.py module.

The tests however, do not require the service to be running because a Flask app
is capable of exposing a test client which we can then use as a proxy to send
it requests directly. The test client is created in the tests' setUp() method.
"""

import os
import unittest
import json
import re

import auth_flask


"""
This TestCase class is devoted to demonstrating and documenting the 
service's API by showing example usage.
"""
class DemonstratesUsage(unittest.TestCase):

    def setUp(self):
        auth_flask.app.testing = True # Suppress sending real emails.
        self.test_client = auth_flask.app.test_client()


    """ 
    The first thing the client must do is request access by POST-ing a request
    to the 'request-access' end point.
    """
    def test_demonstrate_launching_request_for_access(self):
        payload = { 
            'EmailName':'john.doe', # Alleged dnae email owner.
            # The user will receive an email with a clickable link in it of 
            # this form: a_callback_url/claim_access_jwt_as_text.  You provide 
            # the callback url here.
            'Callback': 'http::/myhost/my_callback_path'
        } 
        response = self.test_client.post(
            '/request-access', 
            data = json.dumps(payload), 
            content_type='application/json')
        # All you get back is 200 (OK), or 400 (Invalid Request).
        self.assertEqual(response.status_code, 200)


    """ 
    The second step of the process happens when the user clicks on the link on
    the email they receive. Their email client will bring up a browser window
    pointing at whatever web app the client specified in the call back URL in
    the previous step. Again likely a javascript web app.
    """
    def test_demonstrate_using_the_claim_access_jwt_to_claim_access(self):
        # We can't receive the email in this test, so we'll cheat, and ask
        # a helper function exposed by the service to tell us what the 
        # clickable link would be.
        callback = '/mycallback_url'
        email_clickable_link_url = \
            auth_flask.make_clickable_link_url(callback)

        # Harvest the claim access token from the URL, which will have been
        # structured like this:
        # /mycallback_url/the_token_as_text

        claim_access_token = email_clickable_link_url.replace(
            callback + '/', '')
        # Send a POST request to the 'claim-access' endpoint to receive 
        # back an 'access_granted' JWT.
        payload = { 
            'ClaimAccessToken': claim_access_token
        } 
        response = self.test_client.post(
            '/claim-access', 
            data = json.dumps(payload), 
            content_type='application/json')
        # For this test we should get OK, but the code can return
        # 401 (Not Authorised) - with an explanation in the body.
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.data.decode('utf-8'))
        access_granted_token = response_json['Token']

        # The client should save the access granted token for subsequent use,
        # as illustrated below.

"""
The first step that clients using the authentiation service must take is
to request access using the 'request_access' end point. This class contains the
units tests for this end point.
"""
class RequestAccessEndPointTestCase(unittest.TestCase):

    def setUp(self):
        # In addtition to Flask's usual test-mode behaviours, this suppresses 
        # real emails from being sent by the flask_mail package.
        auth_flask.app.testing = True
        self.test_client = auth_flask.app.test_client()
        self.mail = auth_flask.mail

    """
    The _REQUEST_ACCESS end point is designed to return nothing
    other than a 200 (OK) return code when the request is properly formed..
    """
    def test_response_is_empty_for_properly_formed_request(self):
        response = self.test_client.post(_REQUEST_ACCESS,
            data = json.dumps(_PROPERLY_FORMED_REQUEST_PAYLOAD), 
            content_type='application/json')

        self.assertEqual(
            response.status_code, 200, 'Wrong html response code.')
        self.assertEqual(
            b'', response.data, 'Response data should be empty string')


    """
    The _REQUEST_ACCESS end point is designed to return 400 (Invalid Request)
    return code when the request is improperly formed.
    """
    def test_response_is_invalid_request_for_malformed_request(self):
        response = self.test_client.post(_REQUEST_ACCESS,
            data = json.dumps(MALFORMED_REQUEST_PAYLOAD), 
            content_type='application/json')

        self.assertEqual(
            response.status_code, 400, 'Wrong html response code.')
        self.assertTrue(b'Failed to parse payload' in response.data)
        self.assertTrue(b'EmailName' in response.data)

    """
    Most of the business logic behind this end point is concerned with 
    building a complex URL to include as an href link in an email, so
    we check it is built right with this test..
    """
    def test_email_msg_is_built_correctly_for_properly_formed_request(self):

        # The flask app is set to testing mode in the setup method, which 
        # will cause flask mail to suppress the sending of real mails. But the
        # mail package offers to 'record' virtually-sent mails for us 
        # like this...
        with self.mail.record_messages() as outbox:

            # Send the request that will cause the verification email to
            # get sent.
            response = self.test_client.post(_REQUEST_ACCESS,
                data = json.dumps(_PROPERLY_FORMED_REQUEST_PAYLOAD), 
                content_type='application/json')

            # Ensure a mail got sent by retreiving it.
            self.assertEqual(len(outbox), 1)
            email = outbox[0]
            
            # Scrutinise the mail
            subject = email.subject
            html_content = email.html
            self.assertEqual(subject, 'Please confirm your email address.')

            # Delegate the scrutiny of the email's contents to a helper
            # function..
            self._scrutinise_email_html_content(html_content)


    #-------------------------------------------------------------------------
    # Internal helper methods
    #-------------------------------------------------------------------------

    def _scrutinise_email_html_content(self, html_content):

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
                href_content.startswith(_EXAMPLE_CALLBACK + '/'))

            # Isolate what follows; which should be the JWT as text.
            jwt_portion = href_content.replace(_EXAMPLE_CALLBACK + '/', '')

            # Validate the JWT - delegating to a helper in the implementation
            # module. (Raises exception on validation failure).
            auth_flask.assert_claim_access_token_is_valid(jwt_portion)



# Private constants used internally only.

_REQUEST_ACCESS = '/request-access'

_EXAMPLE_CALLBACK = 'some url'


MALFORMED_REQUEST_PAYLOAD = { 
    'unexpected_key':'john.doe',
    'Callback': _EXAMPLE_CALLBACK
} 

_PROPERLY_FORMED_REQUEST_PAYLOAD = { 
    'EmailName':'john.doe',
    'Callback': _EXAMPLE_CALLBACK
} 

if __name__ == '__main__':
    unittest.main()
