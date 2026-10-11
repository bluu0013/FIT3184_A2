"""Request authentication. Owner: Member B (agree the token contract with Member A, who owns the
Lambda side that forwards the token and the shared key).

Two ways in:
  1. Authorization: Bearer <Cognito ID or access token>, verified against the user pool's JWKS.
     Used when a signed-in user's request is forwarded from AWS (search by file, lost pet).
  2. X-Api-Key matching INFERENCE_API_KEY. Used by the S3-triggered ingest Lambda, which has no
     user token.
"""
import hmac
import os

import jwt
from fastapi import Header, HTTPException

_jwks = None


def _issuer():
    region = os.environ.get("COGNITO_REGION", "")
    pool = os.environ.get("COGNITO_USER_POOL_ID", "")
    return f"https://cognito-idp.{region}.amazonaws.com/{pool}"


def verify_token(token):
    """Return the token's claims, or raise jwt.PyJWTError."""
    global _jwks
    if not os.environ.get("COGNITO_USER_POOL_ID"):
        raise jwt.InvalidTokenError("COGNITO_USER_POOL_ID is not configured")
    if _jwks is None:
        _jwks = jwt.PyJWKClient(_issuer() + "/.well-known/jwks.json", cache_keys=True)
    key = _jwks.get_signing_key_from_jwt(token).key
    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        issuer=_issuer(),
        options={"verify_aud": False},  # access tokens carry client_id instead of aud
    )
    client_id = os.environ.get("COGNITO_CLIENT_ID", "")
    if client_id and client_id not in (claims.get("aud"), claims.get("client_id")):
        raise jwt.InvalidAudienceError("token was not issued for this app client")
    if claims.get("token_use") not in ("id", "access"):
        raise jwt.InvalidTokenError("unexpected token_use")
    return claims


def require_auth(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    expected = os.environ.get("INFERENCE_API_KEY", "")
    if x_api_key and expected and hmac.compare_digest(x_api_key, expected):
        return {"sub": "service:ingest"}
    if authorization and authorization.lower().startswith("bearer "):
        try:
            return verify_token(authorization[7:])
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail=f"invalid token: {exc}") from exc
    raise HTTPException(status_code=401, detail="missing credentials")
