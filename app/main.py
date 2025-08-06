import os
import sys
import logging
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch

# Add plugins directory to Python path so we can import from kick.py
sys.path.append("/app/plugins")
from kick import get_kick_stream_info

# Configure logging with timestamps and log levels
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StreamPlatform(ABC):
    """Abstract base class for streaming platforms"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def setup_client(self):
        """Initialize the platform API client"""
        pass

    @abstractmethod
    async def is_stream_live(self, channel: str) -> tuple[bool, Optional[Any]]:
        """Check if a stream is live. Returns (is_live, stream_data)"""
        pass

    @abstractmethod
    def get_download_command(
        self, channel: str, stream_data: Any, output_file: str
    ) -> List[str]:
        """Get the streamlink command for downloading the stream"""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get the platform name for logging"""
        pass

    @abstractmethod
    def get_platform_shortname(self) -> str:
        """Get the platform shortname for the output file"""
        pass

    def get_stream_title(self, stream_data: Any) -> str:
        """Extract stream title from stream data - default implementation"""
        return "Live Stream"


class TwitchPlatform(StreamPlatform):
    """Twitch streaming platform implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.twitch = None

    async def setup_client(self):
        """Initialize the Twitch API client with authentication"""
        self.twitch = await Twitch(
            self.config["client_id"], self.config["client_secret"]
        )
        await self.twitch.authenticate_app([])
        self.twitch.auto_refresh_auth = False
        logger.info("🎮 Successfully authenticated with Twitch API")

    async def is_stream_live(self, channel: str) -> tuple[bool, Optional[Any]]:
        """Check if a Twitch stream is live"""
        try:
            # Get user ID from username
            user = await first(self.twitch.get_users(logins=[channel]))
            if not user:
                logger.warning(f"⚠️ Could not find Twitch user: {channel}")
                return False, None

            stream = await first(self.twitch.get_streams(user_id=user.id))
            return bool(stream), stream

        except Exception as e:
            logger.error(f"❌ Error checking Twitch status for {channel}: {str(e)}")
            return False, None

    def get_download_command(
        self, channel: str, stream_data: Any, output_file: str
    ) -> List[str]:
        """Get streamlink command for Twitch"""
        return [
            "streamlink",
            "--twitch-api-header",
            f'Authorization={self.config["oauth_token"]}',
            "--stream-segment-threads",
            "5",
            "--twitch-disable-ads",
            "--retry-max",
            "10",
            "--retry-streams",
            "30",
            "--output",
            output_file,
            f"https://twitch.tv/{channel}",
            "best",
        ]

    def get_platform_name(self) -> str:
        return "Twitch"

    def get_platform_shortname(self) -> str:
        return "ttv"

    def get_stream_title(self, stream_data: Any) -> str:
        """Extract stream title from Twitch stream data"""
        print(stream_data)
        if stream_data and hasattr(stream_data, "title"):
            return stream_data.title
        return "Live Stream"


class KickPlatform(StreamPlatform):
    """Kick streaming platform implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    async def setup_client(self):
        """Initialize the Kick API client"""
        logger.info("⚡ Successfully initialized Kick platform")

    async def is_stream_live(self, channel: str) -> tuple[bool, Optional[Any]]:
        """Check if a Kick stream is live using our kick.py helper"""
        try:
            # Use our helper function from kick.py to get stream info
            stream_info = get_kick_stream_info(channel)

            if stream_info and stream_info.get("is_live"):
                return True, stream_info
            else:
                return False, None

        except Exception as e:
            logger.error(f"❌ Error checking Kick status for {channel}: {str(e)}")
            return False, None

    def get_download_command(
        self, channel: str, stream_data: Any, output_file: str
    ) -> List[str]:
        """Get streamlink command for Kick using the plugin"""
        return [
            "streamlink",
            "--plugin-dirs",
            "/app/plugins",  # Where we'll place the Kick plugin
            "--retry-max",
            "10",
            "--retry-streams",
            "30",
            "--output",
            output_file,
            f"https://kick.com/{channel}",
            "best",
        ]

    def get_platform_name(self) -> str:
        return "Kick"

    def get_platform_shortname(self) -> str:
        return "kick"

    def get_stream_title(self, stream_data: Any) -> str:
        """Extract stream title from Kick stream data"""
        if isinstance(stream_data, dict) and "session_title" in stream_data:
            return stream_data["session_title"]
        return "Kick Live Stream"


class StreamArchiver:
    def __init__(self):
        """Initialize the StreamArchiver with configuration from environment variables."""
        # Detect which platforms are configured
        self.platforms = self._initialize_platforms()
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "30"))

        # Set up paths
        self.output_dir = "/output"

        # Dictionary to track active downloads
        self.active_downloads = {}

        # Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)

        # Validate configuration
        self._validate_config()

    def _initialize_platforms(self) -> Dict[str, tuple[StreamPlatform, List[str]]]:
        """Initialize configured streaming platforms"""
        platforms = {}

        # Check for Twitch configuration
        twitch_client_id = os.getenv("TWITCH_CLIENT_ID")
        twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        twitch_oauth_token = os.getenv("TWITCH_OAUTH_TOKEN")
        twitch_channels = (
            os.getenv("TWITCH_CHANNELS", "").split(",")
            if os.getenv("TWITCH_CHANNELS")
            else []
        )

        if (
            twitch_client_id
            and twitch_client_secret
            and twitch_oauth_token
            and twitch_channels
        ):
            twitch_config = {
                "client_id": twitch_client_id,
                "client_secret": twitch_client_secret,
                "oauth_token": twitch_oauth_token,
            }
            platforms["twitch"] = (
                TwitchPlatform(twitch_config),
                [ch.strip() for ch in twitch_channels if ch.strip()],
            )

        # Check for Kick configuration
        kick_channels = (
            os.getenv("KICK_CHANNELS", "").split(",")
            if os.getenv("KICK_CHANNELS")
            else []
        )

        if kick_channels:
            # Kick doesn't require authentication tokens for basic channel monitoring
            kick_config = {}
            platforms["kick"] = (
                KickPlatform(kick_config),
                [ch.strip() for ch in kick_channels if ch.strip()],
            )

        return platforms

    def _validate_config(self):
        """Validate that at least one platform is configured."""
        if not self.platforms:
            raise ValueError(
                "No streaming platforms configured. Please set either:\n"
                "- Twitch: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_OAUTH_TOKEN, TWITCH_CHANNELS\n"
                "- Kick: KICK_CHANNELS\n"
                "- Or both for multi-platform support"
            )

        # Validate Twitch OAuth token format if present
        for platform_name, (platform, channels) in self.platforms.items():
            if platform_name == "twitch" and "oauth_token" in platform.config:
                if not platform.config["oauth_token"].startswith("oauth:"):
                    raise ValueError("TWITCH_OAUTH_TOKEN must start with 'oauth:'")

    async def setup_platforms(self):
        """Initialize all configured platforms"""
        for platform_name, (platform, channels) in self.platforms.items():
            await platform.setup_client()

    async def check_stream_status(self):
        """Check if monitored channels are live and manage downloads accordingly."""
        for platform_name, (platform, channels) in self.platforms.items():
            for channel in channels:
                channel_key = f"{platform_name}:{channel}"
                try:
                    is_live, stream_data = await platform.is_stream_live(channel)

                    if is_live and channel_key not in self.active_downloads:
                        # Stream is live and not being recorded
                        title = platform.get_stream_title(stream_data)
                        logger.info(
                            f"🔴 Starting download for {platform.get_platform_name()} channel {channel} - {title}"
                        )
                        await self._start_download(
                            platform_name, platform, channel, stream_data
                        )

                    elif not is_live and channel_key in self.active_downloads:
                        # Stream ended
                        logger.info(
                            f"⏹️ Stream ended for {platform.get_platform_name()} channel {channel} - stopping download"
                        )
                        self._stop_download(channel_key)

                except Exception as e:
                    logger.error(
                        f"❌ Error checking status for {platform.get_platform_name()} channel {channel}: {str(e)}"
                    )

    async def _start_download(
        self,
        platform_name: str,
        platform: StreamPlatform,
        channel: str,
        stream_data: Any,
    ):
        """
        Start downloading a stream using streamlink.

        Args:
            platform_name (str): The platform name (twitch/kick)
            platform (StreamPlatform): The platform implementation
            channel (str): The channel name
            stream_data: Stream object from platform API
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        title = platform.get_stream_title(stream_data)
        safe_title = (
            title.replace("/", "_").replace("\\", "_")[:200]
            if title
            else "Unknown Title"
        )
        filename = f"{timestamp} {platform.get_platform_shortname()} {channel} {safe_title}.mp4"
        output_file = os.path.join(self.output_dir, filename)

        # Get platform-specific streamlink command
        streamlink_command = platform.get_download_command(
            channel, stream_data, output_file
        )

        channel_key = f"{platform_name}:{channel}"
        try:
            # Start streamlink process
            self.active_downloads[channel_key] = await asyncio.create_subprocess_exec(
                *streamlink_command
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to start download for {platform.get_platform_name()} channel {channel}: {str(e)}"
            )
            self._stop_download(channel_key)

    def _stop_download(self, channel_key: str):
        """Stop and cleanup active downloads."""
        if channel_key in self.active_downloads:
            try:
                self.active_downloads[channel_key].terminate()
            except (ProcessLookupError, OSError):
                # Process already terminated or doesn't exist
                pass
            del self.active_downloads[channel_key]

    async def run(self):
        """Main execution loop."""
        await self.setup_platforms()

        # Log which platforms and channels we're monitoring
        platform_info = []
        for platform_name, (platform, channels) in self.platforms.items():
            platform_info.append(
                f"{platform.get_platform_name()}: {', '.join(channels)}"
            )

        logger.info(
            f"🚀 Starting Stream Archiver - monitoring {' | '.join(platform_info)}"
        )

        while True:
            try:
                await self.check_stream_status()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in main loop: {str(e)}")
                # Wait a bit before retrying after an error
                await asyncio.sleep(5)


if __name__ == "__main__":
    archiver = StreamArchiver()
    asyncio.run(archiver.run())
