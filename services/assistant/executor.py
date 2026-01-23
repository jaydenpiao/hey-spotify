"""Intent executor - executes parsed intents."""
from services.intent.schema import Intent, IntentType, IntentResponse
from services.spotify import devices, playback, search
from services.assistant.resolver import resolve_track_uri
from core.errors import NoActiveDeviceError, SpotifyAPIError
from core.logging import get_logger

logger = get_logger(__name__)


async def execute_intent(user_id: str, intent: Intent) -> IntentResponse:
    """Execute a parsed intent.
    
    Args:
        user_id: User ID
        intent: Parsed intent
        
    Returns:
        Intent response
    """
    try:
        if intent.intent == IntentType.GET_DEVICES:
            device_list = await devices.get_devices(user_id)
            if not device_list:
                return IntentResponse(
                    success=True,
                    message="No devices found. Open Spotify on a device to see it here.",
                    data={"devices": []}
                )
            
            device_names = [f"{d.name} ({'active' if d.is_active else 'inactive'})" 
                           for d in device_list]
            return IntentResponse(
                success=True,
                message=f"Found {len(device_list)} device(s): " + ", ".join(device_names),
                data={"devices": [d.model_dump() for d in device_list]}
            )
        
        elif intent.intent == IntentType.GET_NOW_PLAYING:
            state = await playback.get_current_playback(user_id)
            if not state or not state.item:
                return IntentResponse(
                    success=True,
                    message="Nothing is currently playing",
                    data=None
                )
            
            track = state.item
            artists = ", ".join(a.name for a in track.artists)
            status = "Playing" if state.is_playing else "Paused"
            message = f"{status}: {track.name} by {artists} on {state.device.name}"
            
            return IntentResponse(
                success=True,
                message=message,
                data=state.model_dump()
            )
        
        elif intent.intent == IntentType.PAUSE:
            await playback.pause(user_id, device_id=intent.args.device_id)
            return IntentResponse(
                success=True,
                message="Playback paused"
            )
        
        elif intent.intent == IntentType.RESUME:
            await playback.resume(user_id, device_id=intent.args.device_id)
            return IntentResponse(
                success=True,
                message="Playback resumed"
            )
        
        elif intent.intent == IntentType.SKIP_NEXT:
            await playback.skip_next(user_id, device_id=intent.args.device_id)
            return IntentResponse(
                success=True,
                message="Skipped to next track"
            )
        
        elif intent.intent == IntentType.SKIP_PREV:
            await playback.skip_previous(user_id, device_id=intent.args.device_id)
            return IntentResponse(
                success=True,
                message="Skipped to previous track"
            )
        
        elif intent.intent == IntentType.PLAY:
            if not intent.args.query and not intent.args.track_uri:
                # Just resume
                await playback.resume(user_id, device_id=intent.args.device_id)
                return IntentResponse(
                    success=True,
                    message="Playback resumed"
                )
            
            # Resolve track if query provided
            track_uri = intent.args.track_uri
            if intent.args.query:
                track_uri = await resolve_track_uri(user_id, intent.args.query)
                if not track_uri:
                    return IntentResponse(
                        success=False,
                        message=f"No tracks found for: {intent.args.query}"
                    )
            
            # Start playback
            await playback.play(
                user_id,
                track_uri=track_uri,
                device_id=intent.args.device_id
            )
            
            return IntentResponse(
                success=True,
                message=f"Playing: {intent.args.query or 'track'}",
                data={"track_uri": track_uri}
            )
        
        elif intent.intent == IntentType.QUEUE:
            if not intent.args.query and not intent.args.track_uri:
                return IntentResponse(
                    success=False,
                    message="Please specify what to queue"
                )
            
            # Resolve track if query provided
            track_uri = intent.args.track_uri
            if intent.args.query:
                track_uri = await resolve_track_uri(user_id, intent.args.query)
                if not track_uri:
                    return IntentResponse(
                        success=False,
                        message=f"No tracks found for: {intent.args.query}"
                    )
            
            # Add to queue
            await playback.add_to_queue(user_id, track_uri, device_id=intent.args.device_id)
            
            return IntentResponse(
                success=True,
                message=f"Queued: {intent.args.query or 'track'}",
                data={"track_uri": track_uri}
            )
        
        elif intent.intent == IntentType.SEARCH:
            if not intent.args.query:
                return IntentResponse(
                    success=False,
                    message="Please specify what to search for"
                )
            
            tracks = await search.search_tracks(user_id, intent.args.query, limit=5)
            if not tracks:
                return IntentResponse(
                    success=True,
                    message=f"No results found for: {intent.args.query}",
                    data={"tracks": []}
                )
            
            track_list = [f"{t.name} by {', '.join(a.name for a in t.artists)}" 
                         for t in tracks]
            message = f"Found {len(tracks)} tracks:\n" + "\n".join(f"{i+1}. {t}" 
                                                                     for i, t in enumerate(track_list))
            
            return IntentResponse(
                success=True,
                message=message,
                data={"tracks": [t.model_dump() for t in tracks]}
            )
        
        elif intent.intent == IntentType.SET_VOLUME:
            if intent.args.volume_percent is None:
                return IntentResponse(
                    success=False,
                    message="Please specify volume level (0-100)"
                )
            
            await playback.set_volume(
                user_id,
                intent.args.volume_percent,
                device_id=intent.args.device_id
            )
            
            return IntentResponse(
                success=True,
                message=f"Volume set to {intent.args.volume_percent}%"
            )
        
        elif intent.intent == IntentType.UNKNOWN:
            return IntentResponse(
                success=False,
                message="I didn't understand that. Try: play <song>, pause, devices, now playing"
            )
        
        else:
            return IntentResponse(
                success=False,
                message=f"Intent {intent.intent} not yet implemented"
            )
    
    except NoActiveDeviceError as e:
        return IntentResponse(
            success=False,
            message=str(e)
        )
    except SpotifyAPIError as e:
        logger.error(f"Spotify API error: {e}")
        return IntentResponse(
            success=False,
            message=f"Spotify error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error executing intent: {e}", exc_info=True)
        return IntentResponse(
            success=False,
            message=f"Error: {str(e)}"
        )
