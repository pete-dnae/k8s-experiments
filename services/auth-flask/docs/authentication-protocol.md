# Authentication Protocol (High Level)

This document is targeted at people who understands the principles and
capabilities of Jason Web Tokens (JWT), and of a REST API. It is written on the
assumption that you have read and assimilated the documents about the security
model, and the potential user experience. It is high level, and defers the
detailed documentation of the REST API to documentation in the code.

# Client Apps

For the user experience described in the sister document, the client app referred
to below will be the DNAe web gui app, and its language javascript. But it must 
be remembered that:

- the client app is not known to the authentication service (it is dependency 
  injected as a URL via an environment variable)
- while the client must be something that a browser can run from a link in an
  email message, we should not assume that it is a GUI app
- nor that it is javascript

# Requesting Access

Clients request access by POSTING to this authentication service at a dedicated
<request-access> end point. The payload is:
- the user's alleged email address (just the name part).
- the URL that the requester wants to handle the next leg of the process on the
  client side (Ref 001).

The end point handler responds first by composing and sending an email to
<their-name>@dnae.com that contains an http link for them to click. Then it
replies to the client's request with an empty response that carries either an OK,
or failure http status code. It does nothing else at this point.

The URL embedded in the clickable link is constructed with two segments to 
serve multiple purposes as follows.

- The URL of the client app for the next leg of the process (Ref 001).
- A JWT that encapsulates: the alleged email address, a 5-minute expiry, and 
  the intended audience when the token is re-presented (<claim-access>).

When the user clicks on the link in their email client, it will bring up their
browser; which will itself run whatever client server is cited by the URL in 
the JWT (Ref 001).

This client software will harvest the JWT from the URL at which it has been
invoked and then post that JWT as JSON to the <claim-access> end point in this
authentication service.

The <claim-access> end point of the authentication service, will perform 
non-repudiation and time based validation of the <claim-access> JWT. When these 
pass it will reply with a new JWT that encapsulates "the bearer of this token is
hereby granted access", until this <time> is reached. The granularity of the time
will be in seconds to make sure all tokens differ.

If the validation fails, the end point will return the http <not authorised>
code.

The client software will store the <access-is-granted> token client-side for
for its subsequent use (below).

Once a client has in its possession an <access-is-granted> token, it can use
it to access service end points throughout the suite that demand 
"Bearer Token Authorization" authorization.

The client can also detect tokens having expired and react accordingly. They can
do this of their own accord if they wish because the payload of a JWT is not
encrpted and includes the expiry time. Or they can wait until a protected end 
point declines access to discern the same thing.

Need a diagram here...
