"""
A REST API service that handles client authentication for all the services in
this suite. Can be used by front end web guis or any other rest api clients.

Clients can can use it to request access tokens. The other services can use
these tokens to authorize access.

A token is issued when a client can prove they own any dnae email address, to be
held by the client's computer for use in subsequent service requests.

REad more about JWT and sec here....

The authentication protocol is as follows:

1) A client requests access to the suite of
services, by posting a message to the <request-access> endpoint, with a 
<dnae-email-name> as payload.  (Likely, but not necessarily  from a front end 
gui.)

2) The server sends a mail to the alleged email address @ dnae.com that includes
a clickable link. When the user clicks on the link from their email client it
will launch a browser window pointing to the URL given by the link.

The security model is that if a person can receive this message sent to a dnae
email address - then they should be trusted (for one month - tbd).

3) The link in the email will have been formulated by the server that sent the
email, to encode the following information in the URL's path - in the form of a
cryptographically protected JWT.

- The email address used.
- A 5 minute window during which the link must be used before it expires.
- The purpose of the JWT - i.e. 'claim access'.

4) The root of the URL will likely be a GUI front end app for this suite of
services that knows what to do next to gain access - but this service doesn't
know or care what that URL is - and requires it be injected via an environment
variable. (See config docco).

5) :w



4) Server replies OK if the email got sent. And apart from that does nothing.
(yet)

5) Some time later, the user clicks the link from the email they received. Which
will take them into their web browser - pointing at the 'claim access' URL in 
from the link.

6) The server receives the request on <claim-access>, and will conduct
non-repudiation, and expiry validation of the token. If these are met, it can be
certain that the sender received the email at a dnae email address. And therefore
access should be granted to the owner of that email address. It then returns a
redirect to the client's browser

7)





access can be granted to the client machine from which the email link was clicked.

   the JWT non-repudiation and data integrity checks pass, and the request has
   not expired.

   To grant access, the server replies to the request, with a newly created
   <acces-granted> JWT in the form of a JSON object. This token has no time
   limit.

   If the server declines to grant access, it replies with ??? access denied
   and logs the error details to stdout.


Weaknesses

    This is designed to not require the back end to know about user identities at
    all. It grants access only to people who at least once at some time in the
    past could receive an email on a DNAe address.

    We are treating such people as intrinsically trustworthy.

    Were they not they could:

    o  Share the clickable link email with an external party and encourage them
       to use it before its 5 minute expiry.

    o  Find the <access_granted> token on their computer and share that
       with external parties. Who with sufficient inside knowledge of where to
       put it on their own computer could gain access.

    o  Continue to access the systems these tokens protect, after they had left
       DNAe.

App Launch and Configuration

    o  A Flask app is a WSGI application and can thus be launched by any 
       WSGI-compliant web server.
    o  The <flask> development server is fine for development purposes - 
       see http://flask.pocoo.org/docs/0.12/quickstart/#a-minimal-application.

    o  The app uses a standard Flask configuration file, which it will load from
       the location specified by the AUTH_FLASK_SETTINGS environment variable.
    o  An example may be found in a sister directory to /services called
       /configs.

"""


# Standard imports
import datetime

# Third party packages
from flask import Flask, request, abort, url_for
from jsonschema import validate
from flask_mail import Mail, Message
import jwt

app = Flask(__name__)
app.config.from_envvar('AUTH_FLASK_SETTINGS')

mail = Mail(app)


#-----------------------------------------------------------------------------
# API 
#-----------------------------------------------------------------------------

@app.route('/request-access', methods=['POST'])
def request_access():
    email_name = _parse_email_name()
    _send_verification_email(email_name)
    return ''


@app.route('/claim-access/<token>', methods=['GET'])
def claim_access(token):
    _validate_token(token) # Replies early with error on validatation failure.
    token = _assemble_access_granted_token()
    return token


#-----------------------------------------------------------------------------
# INTERNAL, IMPLEMENTATION FUNCTIONS
#-----------------------------------------------------------------------------

def _parse_email_name():

    try:
        json = request.get_json()
        validate(json, {
            "type": "object",
            "properties": {
                "EmailName": {
                    "type": "string"
                }
            }
        })
        email_name = json['EmailName']

    except Exception as e:
        # Log exception to stdout.
        abort(400, 'Failed to parse EmailName from the POST PAYLOAD')

    return email_name


def _send_verification_email(email_name):
    recipient = email_name + '@dnae.com'
    html = _assemble_verification_email()
    msg = Message(html=html, subject='Please confirm your email address.', 
            recipients=[recipient])
    print('Email message sent is: %s' % html)
    mail.send(msg)


def _assemble_verification_email():

    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
    payload = {
        'exp': expires_at,
        'aud': _CLAIM_ACCESS_AUDIENCE # aud is a reserved JWT keyword
    }
    encoded_jwt_as_bytes = jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)
    encoded_jwt_as_string = encoded_jwt_as_bytes.decode() # UTF-8
    server_name = app.config['VERIFICATION_EMAIL_CLICKABLE_LINK_URL']
    html_message = """
        If you just requested access to the DNAe software team's web services,
        please click the link below to prove that you own a DNAe email address.
        <p>
        <a href="%s%s/%s"> click here </a>
    """ % (server_name, '/claim-access', encoded_jwt_as_string)
    return html_message


def _validate_token(token):
    # Aborts request with error code 401 (not authorised) if the token fails
    # validation checks.
    try:
        decoded = jwt.decode(token, _SECRET, 
            audience=_CLAIM_ACCESS_AUDIENCE, algorithm=_ALGORITHM)
    except jwt.ExpiredSignatureError:
        abort(401, 
            'The signature on the submitted Claim Access Token has expired.')
    except jwt.InvalidAudienceError :
        abort(401, 
            """The audience cited in the submitted Claim Access Token is 
            not right for this handler.""")

def _assemble_access_granted_token():
    expires_at = datetime.datetime.now() + datetime.timedelta(days=30)
    payload = {
        'exp': expires_at,
        'aud': 'ACCESS_GRANTED' # aud is a reserved JWT keyword
    }
    encoded_jwt_as_bytes = jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)
    encoded_jwt_as_string = encoded_jwt_as_bytes.decode() # UTF-8
    payload = { 'token': encoded_jwt_as_string }
    return payload

# Constants used internally only.

_CLAIM_ACCESS_AUDIENCE = 'claim access audience'
_SECRET = 'foobar'
_ALGORITHM = 'HS256'
