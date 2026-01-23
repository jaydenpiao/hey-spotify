"""PKCE (Proof Key for Code Exchange) implementation for OAuth 2.0."""
import secrets
import hashlib
import base64


def generate_code_verifier(length: int = 128) -> str:
    """Generate a cryptographically random code verifier.
    
    Args:
        length: Length of the verifier (43-128 characters)
        
    Returns:
        Base64 URL-encoded random string
    """
    if not 43 <= length <= 128:
        raise ValueError("Code verifier length must be between 43 and 128")
    
    # Generate random bytes
    code_verifier = secrets.token_urlsafe(length)
    return code_verifier[:length]


def generate_code_challenge(code_verifier: str) -> str:
    """Generate code challenge from verifier using SHA256.
    
    Args:
        code_verifier: The code verifier
        
    Returns:
        Base64 URL-encoded SHA256 hash of the verifier
    """
    # Hash the verifier with SHA256
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    
    # Base64 URL encode (without padding)
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8")
    challenge = challenge.rstrip("=")
    
    return challenge


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code verifier and challenge pair.
    
    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    return verifier, challenge
