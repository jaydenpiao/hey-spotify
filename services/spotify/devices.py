"""Spotify device management."""
from typing import List

from services.spotify.client import SpotifyClient
from services.spotify.models import Device
from core.logging import get_logger

logger = get_logger(__name__)


async def get_devices(user_id: str) -> List[Device]:
    """Get user's available Spotify devices.
    
    Args:
        user_id: User ID
        
    Returns:
        List of devices
    """
    async with SpotifyClient(user_id) as client:
        data = await client.get("/me/player/devices")
        devices = [Device(**device) for device in data.get("devices", [])]
        logger.info(f"Found {len(devices)} devices for user {user_id}")
        return devices


async def transfer_playback(user_id: str, device_id: str, play: bool = False) -> None:
    """Transfer playback to a different device.
    
    Args:
        user_id: User ID
        device_id: Target device ID
        play: Whether to start playing after transfer
    """
    async with SpotifyClient(user_id) as client:
        await client.put(
            "/me/player",
            json={
                "device_ids": [device_id],
                "play": play,
            }
        )
        logger.info(f"Transferred playback to device {device_id}")


async def get_active_device(user_id: str) -> Device | None:
    """Get the currently active device.
    
    Args:
        user_id: User ID
        
    Returns:
        Active device or None
    """
    devices = await get_devices(user_id)
    for device in devices:
        if device.is_active:
            return device
    return None
