# ADR 0004: Authentication Architecture
## Status

### Accepted

## Context

- The application needs an authentication mechanism for API requests. The main options considered were server-side sessions and JSON Web Tokens (JWTs).

- The application uses JWT access tokens. The access token contains the user's ID in the sub claim and is signed using the application's JWT secret.

- JWTs were chosen because they work well for an API architecture without requiring a server-side session table for every authenticated user.

## Decision

- Use short-lived JWT access tokens for API authentication.

- The login endpoint authenticates the user's email and password and issues a signed access token containing the user's UUID as the sub claim.

- Protected endpoints use get_current_user to:

1. Decode and verify the JWT signature.
2. Check token expiration.
3. Validate that the sub claim exists.
4. Convert sub to a UUID.
5. Look up the user in the database.
6. Verify that the user exists and is active.

## JWTs Over Server-Side Sessions

- JWTs were selected over traditional server-side sessions because the application does not need to maintain a session record for every authenticated client.

- With sessions, the server generally stores a session identifier and associated state in a database or cache. Every authenticated request can then depend on that session state.

- With JWTs, the token itself carries the authentication information and can be verified cryptographically without maintaining a session table.

- This simplifies the authentication infrastructure and makes the authentication mechanism suitable for an API.

- However, JWTs are not completely stateless in this application because get_current_user performs a database lookup.

## Revocation Tradeoff

- A signed JWT remains valid until it expires unless the application has some additional mechanism for revocation.

- This creates an important tradeoff.

- If a user is deleted or disabled while their JWT is still valid, simply verifying the JWT would allow the request to continue until the token expires.

- The application therefore queries the database during authentication.

- This allows the application to immediately reject:

1. deleted users;
2. disabled users;
3. users whose accounts should no longer have access.

- The cost is that authenticated requests require a database lookup, so the system does not receive the full performance benefit of a completely stateless JWT design.

- The lookup uses the user's UUID as the primary key through db.get(User, user_id), making it an inexpensive indexed lookup. At the application's current scale, this cost is small compared with the work performed by endpoints such as chat requests that may wait significantly longer for an LLM response.

- If this lookup becomes a meaningful performance bottleneck, a short-TTL Redis cache could be introduced for user authentication state.

- The decision is therefore to prioritize correctness and immediate account revocation over strict statelessness.

## Short-Lived Access Tokens and Future Refresh Tokens

- Access tokens should have a relatively short expiration time.

- A short expiration limits the amount of time a stolen access token can be used.

- The application can later introduce refresh tokens to provide a better balance between security and user experience.

- The intended future flow is:

```
Login
  ↓
Short-lived access token
  ↓
API requests
  ↓
Access token expires
  ↓
Refresh token
  ↓
New short-lived access token
```

- Refresh tokens should be handled separately from access tokens and should have stronger revocation controls.

- This is intentionally a future extension rather than part of the current implementation.

## User Account Status

- Users have an is_active field.

- New users are active by default.

- get_current_user rejects both nonexistent users and inactive users with the same generic authentication error.

- This allows an account to be disabled without deleting the user record.

-For example:

```
is_active = True
    → authentication allowed

is_active = False
    → authentication rejected
```

- This provides a simple mechanism for account suspension and abuse prevention.

## Timing and User Enumeration

- Authentication failures should not reveal unnecessary information about whether an account exists.

- For example, the login endpoint returns the same error message for an incorrect email and an incorrect password:

```
Invalid email or password
```

- The application should also avoid introducing a significant timing difference between these cases.

- If an unknown email causes the application to immediately return while a known email causes password hashing to run, an attacker could potentially distinguish existing accounts by measuring response times.

- The authentication implementation should therefore perform password-hash verification in a consistent manner, including for users that do not exist.

- This reduces the usefulness of timing attacks for account enumeration.

- The response message and authentication behavior should therefore avoid revealing whether a particular email address is registered.

## Consequences
### Benefits

- No server-side session table is required.
- JWT signatures provide cryptographic authentication.
- Short token lifetimes limit the impact of stolen access tokens.
- Database lookup allows deleted and disabled users to be rejected before token expiration.
- db.get() provides an efficient primary-key lookup.
- Generic authentication errors reduce account-enumeration information.
- The design leaves room for Redis caching and refresh tokens if the application grows.

### Costs

- Every authenticated request performs a database lookup.
- JWT access tokens cannot be individually revoked without additional state.
- Refresh-token support will require additional design work.
- Authentication must carefully validate JWT payload contents rather than trusting a successfully decoded token.
- Password authentication must be implemented carefully to avoid timing-based account enumeration.

## Alternatives Considered
### Server-Side Sessions

- Server-side sessions would make revocation straightforward because the server controls the session state.

- However, they require maintaining session state and introduce a session-storage dependency for authenticated requests.

## Completely Stateless JWT Authentication

- A completely stateless implementation would verify the JWT without querying the database.

- This would reduce database traffic but would allow a valid token belonging to a deleted or disabled user to remain usable until expiration.

- This tradeoff was rejected because immediate account invalidation is more important for this application.

## Long-Lived Access Tokens

- Long-lived access tokens would reduce the frequency of re-authentication but increase the damage caused by a stolen token.

- This was rejected in favor of short-lived access tokens with refresh tokens as a future improvement.

## Summary

- The application uses short-lived JWT access tokens because they provide a simple authentication mechanism for the API without requiring a server-side session table.

- The application deliberately performs a database lookup in get_current_user. This gives up some of the statelessness advantage of JWTs but allows deleted and disabled accounts to be rejected immediately.

- At the current scale, the primary-key database lookup is considered an acceptable cost compared with the application's dominant workloads.

- If authentication lookups become a measurable bottleneck, caching can be introduced. Refresh tokens can also be added later to improve the user experience while retaining short-lived access tokens.

- The overall priority is correctness and security rather than pursuing statelessness as an end in itself.    

