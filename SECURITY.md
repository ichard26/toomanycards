# Just a couple of notes on security...

First of all, TooManyCards (TMC) is the first web application I've built.

Furthermore, I am neither a professional software engineer nor an experienced backend or
frontend developer.

Lastly, in the pursuit of learning, I am rolling my own solutions for many things,
**including authentication**.

... so it's basically a given that TMC will have vulnerabilities. I'm trying to write a
decently secure webapp, but in all honestry, I don't really know what I'm doing :)

**Please don't submit any confidential or personal information to TMC.**

If you discover a security vulnerability in TMC, please let me know! Otherwise, please
enjoy my (probably naive) notes on the security posture of TMC. 🌺

## How authentication is handled

> TMC's authentication design came from [this dev.to article][dev-to-auth].

TMC uses both access tokens and refresh cookies for authentication. Upon logging in, TMC's
API returns an access token and a refresh cookie.

Access tokens are used to authenticate with the API. They are short-lived and only stored
in memory to avoid CSRF (and localStorage attacks). Once expired, the frontend MUST
request a new access token (POST `/api/refresh-session`) using the refresh 🍪.

The 🍪 is secured with the `HttpOnly`, `SameSite=lax`, and `Secure` flags. And since it can
only access the `/api/refresh-session` endpoint, a CSRF wouldn't be able to do anything
than generate a new access token that's unreadable due to the Same Origin Policy.

On the first visit, the frontend will attempt refreshing the session to obtain a new
session ID for future use. If the user has logged in previously, the refresh 🍪 will be
passed along, allowing the refresh request to succeed. Otherwise, the API will return 401
Unauthorized and logging in will be required.

The access token is bound to the refresh 🍪. Refreshing the access token will invalidate
the previous access token bound to the 🍪 regardless if it has expired or not. Both tokens
are generated from a (presumably high quality) CSPRNG via the
[`secrets.token_hex()`][token_hex] function.

> **Note**: yes, I know this sounds inefficient and janky, but it's easy to implement and
> seems reasonably secure. I'm aware SSR is probably infeasible with this design.

On the sign-up side, passwords are salted and hashed using the [passlib] library and
bcrypt algorithm.

**Summary:** TMC's authentication implementation is _reasonably_ secure against CRSF and
session prediction/fixation, however, the session ID can theoretically be stolen via XSS.
Fortunately, that should not pose an issue (and for what it's worth, I'd have other
problems if TMC was vulnerable to XSS).

## Notes on potential attacks

<!--

# https://security.stackexchange.com/questions/116113/rate-limit-login-attempts-count-by-ip-or-username
# https://www.stavros.io/posts/authentication-and-rate-limiting/
# https://www.toptal.com/cyber-security/10-most-common-web-security-vulnerabilities
# https://owasp.org/www-community/attacks/
# https://cheatsheetseries.owasp.org/
# https://codahale.com/a-lesson-in-timing-attacks/
# https://developer.okta.com/blog/2017/06/21/what-the-heck-is-oauth
# https://auth0.com/intro-to-iam/what-is-oauth-2

-->

### XSS

... TBW

### Cross-Site Request Forgery (CSRF)

The [authentication scheme described earlier](#how-authentication-is-handled) is secure
against CSRF. The access token required to use authenticated endpoints is stored in memory
and must be given explicitly in the `Authorization` header.

### Server-Side Request Forgery (SSRF)

TMC's backend (web server + API) does not perform requests so SSRF should not be a
concern.

### Session fixation (Login CSRF)

Continuing from the
[Authentication discussion from earlier](#how-authentication-is-handled), a less obvious
form of session fixation attack is when an user unwittingly logs in as the attacker.

This can be either be achieved by cookie overwriting or Login CSRF. I'll assume the former
is infeasible by assuming the domain and its subdomains are not compromised *and* that the
["Strict Secure Cookies" draft specification][strict-secure-cookies] has been implemented
(which is true for Chrome and Firefox). <!-- TODO: actually validate this claim -->

Login CSRF is typically possible as there are quite a few ways a malicious site can submit
unwanted requests with parameters or form data, including sign-in credentials. To avoid a
malicious site forcing the browser to log into an attacker controlled account, requests to
`/api/login` MUST contain a `X-CSRF-Protection` header. This relies on the fact that
current implementations of the SOP prevent cross-origin requests from containing custom
headers. This could change so this mitigation isn't perfect, but it's good enough.

### SQL injection

TMC's API uses sqlite3 parameter placeholders to avoid SQL injection issues.

### Timing attacks

While password checks are handled by the [passlib] library and consequently are resistant
to timing attacks, no other measures have been taken to avoid timing attacks in other
parts of the API (including authentication).

For example, it is probably possible to infer whether an username is registered by
checking how long `/api/login` takes to respond with 401 Unauthorized (although
`/api/signup` already leaks this anyway).

## Notes on defense in depth mitigations

Nothing here is meant to be bullet-proof, but these should make TMC harder to abuse and
attack.

> Note: these items are things I want to implement/add (when I have time and sufficient
> motivation down the road)

- Referer and Origin header checks
- IP/User-agent checks (forced refresh)

### HTTP security headers

- A somewhat strong content security policy is place (notably `unsafe-inline` styles are
  still allowed)
- `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()`
- `X-Content-Type-Options: nosniff`

### Rate limiting (and other limits)

To avoid abusive behaviour (or at least, limit their impact), most if not all operations
that add data to the DB have absolute limits or are rate limited.

- User, deck, and card fields are validated and must conform to length minimums and
  maximums
- An user can own at most 50 decks, and each deck can at most contain 100 cards
- An user can only have at most 50 registered sessions at once
- Invalid user logins are rate limited by request and username independently, after which
  all login attempts are blocked until the rate limit expires
- User sign-ups are rate limited by request IP

[dev-to-auth]: https://dev.to/cotter/localstorage-vs-cookies-all-you-need-to-know-about-storing-jwt-tokens-securely-in-the-front-end-15id
[passlib]: https://passlib.readthedocs.io/en/stable/
[strict-secure-cookies]: https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-cookie-alone-01
[token_hex]: https://docs.python.org/3/library/secrets.html#secrets.token_hex
