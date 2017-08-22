/*

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

    This is designed to not require the back end to know about user identities
at all. It grants access only to people who at least once at some time in the
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
    "net/http"
    "io/ioutil"
    "encoding/json"
    "fmt"
    "errors"

	"gopkg.in/gomail.v2"
)


func handle_request_access(w http.ResponseWriter, r *http.Request) {

    // What DNAe email address does the client claim to control?

    emailName, err := getNameFromRequestPayload(r)
    if err != nil {
        panic(err)
    }
    fmt.Printf("emailName parsed: %v\n", emailName)

    // Make an access-claim token to include in the verification email
    // we send to the user.

    access_claim_tkn, err := makeAccessClaimToken()
    if err != nil {
        panic(err)
    }

    // Send the verification email to the user.

    if err = sendVerificationEmail(emailName, access_claim_tkn); err != nil {
        send internal system error or silence with log?
    }
    return ok code
}


func getNameFromRequestPayload(r *http.Request) (name string, err error){

    payload, err := ioutil.ReadAll(r.Body)
    if err != nil {
        return "", err
    }

    var deserialized struct {
        EmailName  string
    }
    
    err = json.Unmarshal(payload, &deserialized)
    if err != nil {
        return "", err
    }

    if deserialized.EmailName == "" {
        return "", errors.New("Cannot read email name from request payload.")
    }
    return deserialized.EmailName, err
}


func send_mail() {

	m := gomail.NewMessage()

	m.SetHeader("From", "peterhoward42@gmail.com")
	m.SetHeader("From", "pete.howard@dnae.com")
	m.SetHeader("To", "peterhoward42@gmail.com")
	m.SetHeader("Subject", "Hello from SES sent message")
	m.SetBody("text/html", "Hello <b>Bob</b> and <i>Cora</i>!")

    // These AWS SES SMTP credentials were created in the AWS console.
	smtp_usr := "AKIAJA7X6HNYWNKXMBKA"
	smtp_pass := "AuSWIed+FQLKEjciadCXFAvx+oqDfLUurMnktMdvRJ9g"

	// d := gomail.NewDialer("smtp.example.com", 587, "user", "123456")
	d := gomail.NewDialer("email-smtp.eu-west-1.amazonaws.com", 587, smtp_usr,
		smtp_pass)

	if err := d.DialAndSend(m); err != nil {
		panic(err)
	}
}

func main() {
    http.HandleFunc("/request-access", handle_request_access)
    http.ListenAndServe(":8080", nil)
}
