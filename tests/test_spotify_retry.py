"""Tests for Spotify client retry logic."""
import pytest
from core.rate_limit import calculate_backoff


def test_calculate_backoff_progression():
    """Test exponential backoff progression."""
    # First attempt
    delay0 = calculate_backoff(0, base_delay=1.0)
    assert 0.75 <= delay0 <= 1.25  # 1.0 ± 25% jitter
    
    # Second attempt (should be ~2x)
    delay1 = calculate_backoff(1, base_delay=1.0)
    assert 1.5 <= delay1 <= 2.5  # 2.0 ± 25% jitter
    
    # Third attempt (should be ~4x)
    delay2 = calculate_backoff(2, base_delay=1.0)
    assert 3.0 <= delay2 <= 5.0  # 4.0 ± 25% jitter


def test_calculate_backoff_max_delay():
    """Test that backoff respects max delay."""
    # With high attempt number, should cap at max_delay
    delay = calculate_backoff(10, base_delay=1.0, max_delay=10.0)
    assert delay <= 10.0 * 1.25  # Max + jitter allowance


def test_calculate_backoff_jitter():
    """Test that jitter adds randomness."""
    delays = [calculate_backoff(1, base_delay=1.0) for _ in range(10)]
    
    # All delays should be different (extremely unlikely to be same with jitter)
    unique_delays = set(delays)
    assert len(unique_delays) > 5  # At least some variation
    
    # All should be in expected range
    for delay in delays:
        assert 1.5 <= delay <= 2.5


def test_calculate_backoff_no_negative():
    """Test that backoff never returns negative values."""
    for attempt in range(10):
        delay = calculate_backoff(attempt)
        assert delay >= 0


def test_calculate_backoff_custom_base():
    """Test backoff with custom base delay."""
    delay = calculate_backoff(0, base_delay=2.0)
    assert 1.5 <= delay <= 2.5  # 2.0 ± 25% jitter
    
    delay = calculate_backoff(1, base_delay=2.0)
    assert 3.0 <= delay <= 5.0  # 4.0 ± 25% jitter


# Note: Testing the actual SpotifyClient retry logic would require
# mocking httpx responses, which is more complex. These tests cover
# the backoff calculation logic which is the core of the retry system.
