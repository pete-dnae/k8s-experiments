# Authentication Protocol (High Level)

This document is targeted at people who understands the principles and
capabilities of Jason Web Tokens (JWT), and of a REST API. It is written on the
assumption that you have read and assimilated the documents about the security
model, and the potential user experience. It is high level, and defers the
detailed documentation of the REST API to a separate document.

# Client Apps

The client app referred to here is likely the DNA Web Gui front end code. But it
need not be. Any client could be used that can satisfy the protocol outlined
below.

# Client Requesting Access

Clients request access by POSTING to this authentication service at a dedicated
<request-access> end point. The payload is:
- the user's alleged email address (just the name part).
- a client callback URL that the requester wants to handle the next leg of 
  the process on the client side.

The <request-access> end point handler responds first by composing and sending an
email to <their-name>@dnae.com that contains an http link for them to click. Then
it replies to the client's request with an empty response that carries either an
OK, or failure http status code. It does nothing else at this point.

The URL embedded in the clickable link is constructed in two segments. The first
part is the client callback URL described above, and the second is a JWT in its
URL text form. The JWT encapsulates the following in its payload:

- the alleged email address
- a 5-minute expiry
- the intended audience for when the token is re-presented (<claim-access>).

When the user clicks on the link in their email client, it will bring up their
browser; which will itself run the client app as defined by the callback URL.

This client software will harvest the JWT from the URL at which it has been
invoked and then post that JWT as JSON to the <claim-access> end point in this
authentication service.

The <claim-access> end point will perform non-repudiation and time based
validation of the <claim-access> JWT. When these pass it will reply with a
**new** JWT that encapsulates "the bearer of this token is hereby granted
access", until this <time> is reached. The JWT will also include a 256 byte
randomly generated number, to ensure all tokens issued differ.

If the validation fails, the end point will return the http <not authorised>
code.

The client software, upon receiving a reply that carries an 
<access-is-granted> token will store it client-side for for its subsequent use 
(below).

Once a client has in its possession an <access-is-granted> token, it can use
it to access service end points throughout the suite that demand 
"Bearer Token Authorization" authorization.

The client can also detect tokens having expired and react accordingly. They can
do this of their own accord if they wish, because the payload of a JWT is not
encrpted and includes the expiry time. Or they can wait until a protected end 
point declines access to discern the same thing.
