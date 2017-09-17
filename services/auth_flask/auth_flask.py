"""
A REST API service providing authentication for all the services in
this suite.

The API documentation is provided in the form of dedicated exemplar unit 
tests in auth_flask_examples.py

See other documentation in ./docs directory.
"""


# Standard imports
import datetime

# Third party packages
from flask import Flask, request, abort, url_for, jsonify
from jsonschema import validate
from flask_mail import Mail, Message
import jwt


app = Flask(__name__)
app.config.from_envvar('APP_CONFIG_FILE')

mail = Mail(app)


#-----------------------------------------------------------------------------
# API 
#-----------------------------------------------------------------------------

"""
Clients initiate their request for an access token here.
Payload includes an alleged DNAe email address and the URL the client wishes
to be called as a callback after the email ownership has been confirmed.
Response is an http status code, and an empty body.
"""
@app.route('/request-access', methods=['POST'])
def request_access():
    email_name, client_callback_url = _parse_request_access_payload()
    _send_verification_email(email_name, client_callback_url)
    return ''


"""
This end point is used by the software at the end of the client's callback URL
provided above, and is the second leg of the authentication process.  This
server will have added a <claim-acces> JWT to that URL so the client can
retrieve it. The client should then POST a request to this end point, providing
the JWT as payload.  If the JWT passes integrity and non-repudiation checks,
and the expiry date has not been reached, and the audience properly cites this
end point, then authorisation will be granted. In which case a response is sent
comprising a new <ACCESS-GRANTED> JWT. The client should store this client-side
for subsequent use. Otherwise the repsonse is the http NOT AUTHORISED error
code.
"""
@app.route('/claim-access', methods=['POST'])
def claim_access():
    token = _parse_claim_access_payload()
    _assert_token_is_valid(token, _CLAIM_ACCESS_AUDIENCE )
    token = _assemble_access_granted_token()
    return jsonify(token)


"""
This end point can be used by any of the services in this suite that wish to
allow access only to clients who can present the <ACCESS_GRANTED> tokens that
have been issued by this authenticaion service. It responds with http OK or 
http NOT AUTHORISED.
"""
@app.route('/verify-access-token', methods=['POST'])
def verify_access_token():
    token = _parse_verify_access_payload()
    _assert_token_is_valid(token, _ACCESS_GRANTED_AUDIENCE )
    return ''


#-----------------------------------------------------------------------------
# Methods exposed publicly only to support testing.
#-----------------------------------------------------------------------------

"""
Asserts that a given token, if presented to the claim_access end point would
validate successfully.  We expose this helper function to avoid the need for
leaking the module-scope_SECRET that the JWT is signed with outside this
module.  The outcome is indicated by allowing the exceptions raised inside the
jwt package to be propagated if the validation fails.
"""
def assert_claim_access_token_is_valid(token):
        decoded = jwt.decode(token, _SECRET, 
            audience = _CLAIM_ACCESS_AUDIENCE , algorithms=[_ALGORITHM])

"""
Builds a clickable link URL to go inside a verification email message.
We expose this helper function so that unit tests can pretent they received
the email sent to the user.
"""
def make_clickable_link_url(callback_url):
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
    payload = {
        'exp': expires_at,
        'aud': _CLAIM_ACCESS_AUDIENCE # aud is a reserved JWT keyword
    }
    encoded_jwt_as_bytes = jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)
    encoded_jwt_as_string = encoded_jwt_as_bytes.decode() # UTF-8
    link_url = '%s/%s' % (callback_url, encoded_jwt_as_string)
    return link_url


#-----------------------------------------------------------------------------
# INTERNAL, IMPLEMENTATION FUNCTIONS
#-----------------------------------------------------------------------------

"""
Extracts the required fields from the <REQUEST-ACCESS> request.
Any exceptions raised and trigger an immediate code 400 error with 
an explanation.
"""
def _parse_request_access_payload():
    try:
        json = request.get_json()
        validate(json, {
            "type": "object",
            "properties": {
                "EmailName": { "type": "string" },
                "Callback": { "type": "string", "format": "uri" }
            }
        })
        email_name = json['EmailName']
        callback = json['Callback']
    except Exception as e:
        msg = 'Failed to parse payload: %s\n' % e
        abort(400, msg)
    return email_name, callback


"""
Extracts the required fields from the <CLAIM-ACCESS> request.
Any exceptions raised trigger an immediate code 400 error with 
an explanation.
"""
def _parse_claim_access_payload():
    try:
        json = request.get_json()
        validate(json, {
            "type": "object",
            "properties": {
                "ClaimAccessToken": { "type": "string" },
            }
        })
        claim_access_token = json['ClaimAccessToken']
    except Exception as e:
        msg = 'Failed to parse payload: %s\n' % e
        abort(400, msg)
    return claim_access_token


"""
Extracts the required fields from the <VERIFY-ACCESS> request.
Any exceptions raised and trigger an immediate code 400 error with 
an explanation.
"""
def _parse_verify_access_payload():

    try:
        json = request.get_json()
        validate(json, {
            "type": "object",
            "properties": {
                "Token": { "type": "string" },
            }
        })
        token = json['Token']
    except Exception as e:
        msg = 'Failed to parse payload: %s\n' % e
        abort(400, msg)
    return token


"""
Sends an email confirmation message to the alleged DNAe email address, that
includes a clickable link that encodes the clients callback URL and a
<CLAIM_ACCESS> JWT. Uses Flask Mail under the hood - which takes care of error
handling.
"""
def _send_verification_email(email_name, client_callback_url):
    recipient = email_name + '@dnae.com'
    html = _assemble_verification_email(client_callback_url)
    msg = Message(html=html, subject='Please confirm your email address.', 
            recipients=[recipient])

    # See the flask_mail package (or the unit tests for this module), for how 
    # to suppress the real sending of mails in this call, and how to instead,
    # record the mails that would have been sent - for scrutiny by tests.
    mail.send(msg)


"""
Builds up the html verification email message by building the JWT required and 
combinging it with the client's callback URL for the clickable link in the 
message.
"""
def _assemble_verification_email(client_callback_url):
    link_url = make_clickable_link_url(client_callback_url)
    html_message = """
        If you just requested access to the DNAe software team's web services,
        please click the link below to prove that you own a DNAe email address.
        <p>
        <a href="%s"> click here </a>
    """ % link_url
    return html_message


"""
Validates a JWT token using standard JWT means in the context of the current
request. Responds to the current request immediately with a http 
NOT AUTHORISED code at the first encountered failure. Returns None.
"""
def _assert_token_is_valid(token, intended_audience):
    try:
        decoded = jwt.decode(token, _SECRET, 
            audience=intended_audience, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        abort(401, 
            'The signature on the submitted Claim Access Token has expired.')
    except jwt.InvalidAudienceError :
        abort(401, 
            """The audience cited in the submitted Claim Access Token is 
            not right for this handler.""")


"""
Builds and returns an <ACCESS-GRANTED> JWT.
"""
def _assemble_access_granted_token():
    expires_at = datetime.datetime.now() + datetime.timedelta(days=30)
    payload = {
        'exp': expires_at,
        'aud': _ACCESS_GRANTED_AUDIENCE # aud is a reserved JWT keyword
    }
    encoded_jwt_as_bytes = jwt.encode(
        payload, _SECRET, algorithm=_ALGORITHM)
    encoded_jwt_as_string = encoded_jwt_as_bytes.decode() # UTF-8
    payload = { 'Token': encoded_jwt_as_string }
    return payload


# Private constants used internally only.

_CLAIM_ACCESS_AUDIENCE = 'claim access audience'
_ACCESS_GRANTED_AUDIENCE = 'access granted'
_SECRET = 'I1Oq9W1TQ7' # Arbitrary
_ALGORITHM = 'HS256'
