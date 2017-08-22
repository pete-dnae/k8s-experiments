"""
A REST API service that handles client authentication for all the services in
this suite.

Clients can can use it to request access tokens. The other services can use
these tokens to authorize access.

A token is issued when a client can prove they own any dnae email address, and
will be held by the client's computer for use in subsequent service requests.

The authentication protocol is as follows:

1) Client hits <request-access> endpoint, with <dnae-email-name> as payload.

2) Server composes a <claim-access> JWT that:
    - states its claim to be "claim-access"
    - specifies a time limit of 5 minutes hence

3) Server sends an email to <dnae-email-name>@dnae.com, with a clickable link
   in it that includes both the <claim-access> endpoint and the url-encoded JWT.

   i.e.

   this-server::/claim-access/<claim-access-jwt>

4) Server replies OK if the email got sent.

5) Some time later, the user clicks the link from the email they received.

6) The server receives the request on <claim-access>, and will grant access if
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

"""


from flask import Flask, request, abort
from jsonschema import validate
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_envvar('AUTH_FLASK_SETTINGS')

mail = Mail(app)


#-----------------------------------------------------------------------------
# API ENTRY POINT FUNCTIONS
#-----------------------------------------------------------------------------

@app.route('/request-access', methods=['POST'])
def request_access():
    email_name = parse_email_name()
    send_email_to_dnae_address(email_name)
    return '' # Implicit HTTP OK status.


#-----------------------------------------------------------------------------
# INTERNAL, IMPLEMENTATION FUNCTIONS
#-----------------------------------------------------------------------------

def parse_email_name():

    try:
        json = request.get_json()
        validate(json, {
            "type": "object",
            "properties": {
                "email_name": {
                    "type": "string"
                }
            }
        })
        email_name = json['email_name']

    except Exception as e:
        # Log exception to stdout.
        abort(400, 'Failed to parse email_name from POST JSON')

    return email_name


def send_email_to_dnae_address(email_name):
    html = '<b>hello</b>'
    msg = Message(html, recipients=["peterhoward42@gmail.com"])
    mail.send()
