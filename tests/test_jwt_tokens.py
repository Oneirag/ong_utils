import unittest

from ong_utils.jwt_tokens import decode_jwt_token, decode_jwt_token_expiry
from tests import jwt_token


class TestJwtTokens(unittest.TestCase):

    def test_decode(self):
        """Tests that jwt token is properly decoded"""
        decoded = decode_jwt_token(jwt_token)
        self.assertEqual(decoded['scope'], 'introscpect_tokens, revoke_tokens')

    def test_expiry(self):
        """Tests that expiration is properly decoded"""
        expiry = decode_jwt_token_expiry(jwt_token)
        self.assertEqual(expiry.timestamp(), 1621214688)
