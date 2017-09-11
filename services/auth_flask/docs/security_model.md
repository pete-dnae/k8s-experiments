# Security Model

This document is targeted at a management policy-making audience, and does not
require software / IT knowledge of any depth.

This security model aims to prevent the general public from accessing DNAe's
software tools, once these tools are moved to the cloud as web services. Today
these tools are served from servers on the private corporate network, and anyone
who has access to the corporate network has access to the software. Our software
today does not have any concept built in to it of *users*. Everyone using the
software is treated as being an anonymous user.

We wish *initially* to retain the anonymous user concept, but require people to
prove (just once) that they belong to DNA in order to be granted access.  The
model uses a person's ability to receive an auto-generated verification email to
their_name@dnae.com as proof that they belong to DNAe and to be granted access.

## Vulnerabilities

While the scheme adopts a well adopted pattern, and is (for the most part) robust
from a cryptographic point of view, it does have conceptual vulnerabilities
listed here.

It is the *computer* that the DNAe person uses to verify their email that gets
given access, not the human user. This computer cannot be relied upon to be under
the control of DNAe; it could for example, be the user's personal computer, with
the user having verified their ownership of a DNAe email address using the email
function in the Office 365 web app. Thus any other person who can login to that
computer will be able to access the web software.

The access granted has an expiry date which we can program. The date could be set
so far ahead to be effectively for ever, or for whatever shorter interval we
choose. Maybe one month. In the former case, a user would only ever have to prove
their ownership of a DNAe email address once (per computer). But this makes it
impossible for access to be rescinded for any one individual user. For this
reason, a one month period is often chosen, after which a user is required to
re-verify their email address.

There is a burden of trust on the person responding to the auto-generated
verification email not to share that email with people outside DNAe, because
anyone who clicks on that link during a 5-minute inverval from its time of
emission) will be granted access. (More strictly; their computer will).

The transmission of the auto-generated email is a weak link, because emails
travel over the internet unencrypted, and a skilled malicious third party could
intercept the email and use it (unaltered) to be granted access, instead of the
intended recipient. It should be noted, that this is not any bigger a security
risk than DNAe entrusting routine communications about business sensitive topics
to email.
