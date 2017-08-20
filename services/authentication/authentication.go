/*

A REST API service that clients can can use to request access-granting JWTs for
the other services in the microservices suite.

Any other services in the suite that require access control, can then demand that
the tokens issues by this service be provided by their clients in requests.

It uses email verification to authenticate the client, and access is granted in
the form of a JWT. The system does not store email addresses or details of users.
The email verification is a one-shot authentication exercise, after which the user
email or identity plays no further role.

The authentication protocol is as follows:

1) Client hits <request_access> endpoint, with <dnae-email-name> as payload.

2) Server composes a <claim_access> JWT that:
    - states its claim to be "claim_access"
    - specifies a time limit of 5 minutes hence

3) Server sends an email to <dnae-email-name>@dnae.com, with a clickable link
   in it that includes both the <claim-access> endpoint and the url-encoded JWT.

   i.e.

   this_server::/claim_access/<claim_access_jwt>

4) Server replies OK if the email got sent.

5) Some time in the next 5 minutes, the user clicks the link from the email they
   received.

6) The server receives the request on <claim_access>, and will grant access if
   the JWT non-repudiation and data integrity checks pass, and the request has
   not expired.

   To grant access, the server replies to the request, with a newly created
   <acces_granted> JWT in the form of a JSON object. This token has no time
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
*/

package main

import (
	"gopkg.in/gomail.v2"
)

func main() {
	print("XXXX STARTING\n")

	m := gomail.NewMessage()

	m.setHeader("From", "pretend_user@pretend.org")
	m.SetHeader("To", "success@simulator.amazonses.com")
	m.SetHeader("Subject", "Hello from SES sent message")
	m.SetBody("text/html", "Hello <b>Bob</b> and <i>Cora</i>!")

	smtp_usr := "AKIAJA7X6HNYWNKXMBKA"
	smtp_pass := "AuSWIed+FQLKEjciadCXFAvx+oqDfLUurMnktMdvRJ9g"
	// d := gomail.NewDialer("smtp.example.com", 587, "user", "123456")
	d := gomail.NewDialer("email-smtp.eu-west-1.amazonaws.com", 587, smtp_usr,
		smtp_pass)

	if err := d.DialAndSend(m); err != nil {
		panic(err)
	}
	print("XXXX ENDED\n")

}
