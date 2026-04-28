import hashlib
import base64
import secrets

def generate_code_verifier():
    return secrets.token_urlsafe(64)

def generate_code_challenge(code_verifier):
    sha256 = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256).decode().replace('=', '')

def generate_state():
    return secrets.token_urlsafe(32)