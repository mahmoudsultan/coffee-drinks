import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-h9m4uuyy.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''


def get_token_auth_header():
    authorization_header = request.headers.get('Authorization', None)
    if not authorization_header:
        raise AuthError('Authorization header not provided.', 401)

    authorization_header_parts = authorization_header.split(' ')
    if (len(authorization_header_parts) != 2
       or authorization_header_parts[0].lower() != 'bearer'):
        raise AuthError('Authorization header value is malformed', 401)

    return authorization_header_parts[1]


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string
        is not in the payload permissions array
    return true otherwise
'''


def check_permissions(permission, payload):
    user_permissions = payload['permissions']
    if not user_permissions:
        raise AuthError('User does not have any permissions', 401)

    if permission not in user_permissions:
        raise AuthError('User does not have the required permission', 401)

    return True


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload
'''


def get_rsa_key_for_token(token):
    keys_json_url = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    keys_json = json.loads(keys_json_url.read())

    jwt_header = jwt.get_unverified_header(token)
    used_rsa_key = {}

    for key in keys_json['keys']:
        if key['kid'] == jwt_header['kid']:
            used_rsa_key = {k: key[k]
                            for k in ['kid', 'kty', 'use', 'n', 'e']}

    return used_rsa_key


def verify_decode_jwt(token):
    # GET Keys and find the used key in this JWT from the JWT header
    used_rsa_key = get_rsa_key_for_token(token)

    # If no proper key abort
    if not used_rsa_key:
        raise AuthError('No proper key.', 401)

    # Decode and Verify the JWT signuture
    try:
        jwt_payload = jwt.decode(
            token,
            used_rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )

        print(jwt_payload)

        return jwt_payload
    except jwt.ExpiredSignatureError:
        raise AuthError('Token expired.', 401)
    except jwt.JWTClaimsError:
        raise AuthError('Token issuer or audience is invalid', 401)
    except Exception:
        raise AuthError('Something went wrong while decoding JWT', 401)


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims
        and check the requested permission

    return the decorator which passes the decoded payload
        to the decorated method
'''


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
