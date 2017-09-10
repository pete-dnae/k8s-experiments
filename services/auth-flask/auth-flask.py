"""
A REST API service that handles client authentication for all the services in
this suite.

See documentation in ./docs directory.
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
Responds with an http status code only.

curl --request POST \
  --url http://127.0.0.1:5000/request-access \
  --header 'content-type: application/json' \
  --data '{
        "EmailName": "pete.howard",
        "Callback": "127.0.0.1:5000/claim-access"
    }'

"""
@app.route('/request-access', methods=['POST'])
def request_access():
    email_name, client_callback_url = _parse_request_access_payload()
    _send_verification_email(email_name, client_callback_url)
    return ''


"""
This end point is used by the software at the end of the client's callback URL
provided above, and is the second leg of the authentication process. This server
will have added a <claim-acces> JWT to the URL so the client can retrieve it. The
client should then POST a request to this end point, providing the JWT as payload.
If the JWT passes integrity and non-repudiation checks, and the expiry date has
not been reached, and the audience properly cites this end point, then
authorisation will be granted. In which case a response is sent comprising a 
new <ACCESS-GRANTED> JWT. The client should store this client-side for subsequent
use. Otherwise the repsonse is the http NOT AUTHORISED error code.

curl --request GET \
  --url http://127.0.0.1:5000/claim-access/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJjbGFpbSBhY2Nlc3MgYXVkaWVuY2UiLCJleHAiOjE1MDQwNDMzNjh9.WpHFIdzGkxEz7QWYXSHQq6TYbekGU_nhibD7ID8gQ9g \
  --header 'content-type: application/json'
"""
@app.route('/claim-access/<token>', methods=['GET'])
def claim_access(token):
    _assert_token_is_valid(token, _CLAIM_ACCESS_AUDIENCE )
    token = _assemble_access_granted_token()
    print('Token is: %s' % token)
    return jsonify(token)


"""
This end point can be used by any of the services in this suite that wish to
allow access only to clients who can present the <ACCESS_GRANTED> tokens that
have been issued by this authenticaion service. It responds with http OK or 
http NOT AUTHORISED.

curl --request POST \
  --url http://127.0.0.1:5000/verify-access-token \
  --header 'content-type: application/json' \
  --data '{
          "Token":
          "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhY2Nlc3MgZ3JhbnRlZCIsImV4cCI6MTUwNjYzNTc4M30.QzQJOlRshvyHHkiUTfz7uqIt3En0Hap1fby4sZkbRxc"
    }'


"""
@app.route('/verify-access-token', methods=['POST'])
def verify_access_token():
    token = _parse_verify_access_payload()
    _assert_token_is_valid(token, _ACCESS_GRANTED_AUDIENCE )
    return ''

#-----------------------------------------------------------------------------
# INTERNAL, IMPLEMENTATION FUNCTIONS
#-----------------------------------------------------------------------------

"""
Extracts the required fields from the <REQUEST-ACCESS> request.
Any exceptions raised are logged, and trigger an immediate code 400 error with 
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
        print(msg)
        abort(400, msg)

    return email_name, callback


"""
Extracts the required fields from the <VERIFY-ACCESS> request.
Any exceptions raised are logged, and trigger an immediate code 400 error with 
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
        print(msg)
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
    print('Mail that would be sent:%s\n' % msg)
    #mail.send(msg)


"""
Builds up the html verification email message by building the JWT required and 
combinging it with the client's callback URL for the clickable link in the 
message.
"""
def _assemble_verification_email(client_callback_url):

    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
    payload = {
        'exp': expires_at,
        'aud': _CLAIM_ACCESS_AUDIENCE # aud is a reserved JWT keyword
    }
    encoded_jwt_as_bytes = jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)
    encoded_jwt_as_string = encoded_jwt_as_bytes.decode() # UTF-8
    html_message = """
        If you just requested access to the DNAe software team's web services,
        please click the link below to prove that you own a DNAe email address.
        <p>
        <a href="%s/%s"> click here </a>
    """ % (client_callback_url, encoded_jwt_as_string)
    return html_message


"""
Validates a JWT token using standard JWT means.
Responds to the current request immediately with a http NOT AUTHORISED code at
the first encountered failure. Returns None.
"""
def _assert_token_is_valid(token, intended_audience):
    try:
        decoded = jwt.decode(token, _SECRET, 
            audience=intended_audience, algorithm=_ALGORITHM)
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
    encoded_jwt_as_bytes = jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)
    encoded_jwt_as_string = encoded_jwt_as_bytes.decode() # UTF-8
    payload = { 'Token': encoded_jwt_as_string }
    return payload


# Constants used internally only.

_CLAIM_ACCESS_AUDIENCE = 'claim access audience'
_ACCESS_GRANTED_AUDIENCE = 'access granted'
_SECRET = 'foobar'
_ALGORITHM = 'HS256'
