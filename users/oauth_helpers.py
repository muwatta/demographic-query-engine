import secrets
import hashlib
import base64

def generate_code_verifier():
    return secrets.token_urlsafe(64)

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().replace('=', '')

def generate_state():
    return secrets.token_urlsafe(32)