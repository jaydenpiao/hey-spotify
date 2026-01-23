"""Tests for PKCE implementation."""
import pytest
from services.auth.pkce import (
    generate_code_verifier,
    generate_code_challenge,
    generate_pkce_pair,
)


def test_generate_code_verifier():
    """Test code verifier generation."""
    verifier = generate_code_verifier()
    assert len(verifier) == 128
    assert verifier.replace('-', '').replace('_', '').isalnum()


def test_generate_code_verifier_custom_length():
    """Test code verifier with custom length."""
    verifier = generate_code_verifier(length=64)
    assert len(verifier) == 64


def test_generate_code_verifier_invalid_length():
    """Test code verifier rejects invalid lengths."""
    with pytest.raises(ValueError):
        generate_code_verifier(length=42)  # Too short
    
    with pytest.raises(ValueError):
        generate_code_verifier(length=129)  # Too long


def test_generate_code_challenge():
    """Test code challenge generation."""
    verifier = "test_verifier_1234567890"
    challenge = generate_code_challenge(verifier)
    
    # Challenge should be base64url encoded
    assert challenge.replace('-', '').replace('_', '').isalnum()
    assert '=' not in challenge  # No padding
    
    # Same verifier should produce same challenge
    challenge2 = generate_code_challenge(verifier)
    assert challenge == challenge2


def test_generate_pkce_pair():
    """Test PKCE pair generation."""
    verifier, challenge = generate_pkce_pair()
    
    assert len(verifier) == 128
    assert len(challenge) > 0
    
    # Verify challenge matches verifier
    expected_challenge = generate_code_challenge(verifier)
    assert challenge == expected_challenge


def test_pkce_pair_uniqueness():
    """Test that each pair is unique."""
    pair1 = generate_pkce_pair()
    pair2 = generate_pkce_pair()
    
    assert pair1[0] != pair2[0]  # Different verifiers
    assert pair1[1] != pair2[1]  # Different challenges
