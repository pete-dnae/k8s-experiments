# Overview

This is a web service API that provides authentication services for the suite of 
internet services of which it forms part.

It is based on the "The OAuth 2.0 Authorization Framework: Bearer Token Usage"
standard:  https://tools.ietf.org/html/rfc6750

It adopts Jason Web Tokens (JWT) as its Token standard:
https://en.wikipedia.org/wiki/JWT

It encapsulates a security model that treats users as being anonymous, but
requires them to prove they own a DNAe email address to gain access, thus
denying access to the general public.

See additional documentation in the *docs* sub directory.
