from datetime import datetime
from ong_utils.import_utils import raise_extra_exception
try:
    import jwt
except ModuleNotFoundError:
    raise_extra_exception("jwt")


def decode_jwt_token(access_token: str) -> dict:
    """Decodes access token and returns it as a dict"""
    # Code for jwt 2.x
    if jwt.__version__ >= "2.0.0":
        # Example of checking token expiry time to expire in the next 10 minutes
        alg = jwt.get_unverified_header(access_token)['alg']
        decoded_token = jwt.decode(access_token, algorithms=[alg], options={"verify_signature": False})
    else:
        # code for jwt 1.x
        decoded_token = jwt.decode(access_token, verify=False)

    return decoded_token


def decode_jwt_token_expiry(jwt_token: str) -> datetime:
    """Gets jwt token expiration from token"""
    decoded_token = decode_jwt_token(jwt_token)
    expiry = decoded_token['exp']
    if isinstance(expiry, int):
        token_expiry = datetime.fromtimestamp(expiry)
    else:
        token_expiry = datetime.fromisoformat(expiry)
    return token_expiry

