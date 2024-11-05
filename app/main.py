import os
import time
import logging
from datetime import datetime
import asyncio
import subprocess
import signal
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch

# Configure logging with timestamps and log levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitchArchiver:
    def __init__(self):
        """Initialize the TwitchArchiver with configuration from environment variables."""
        # Load configuration from environment
        self.client_id = os.getenv('TWITCH_CLIENT_ID')
        self.client_secret = os.getenv('TWITCH_CLIENT_SECRET')
        self.oauth_token = os.getenv('TWITCH_OAUTH_TOKEN')
        self.channels = os.getenv('TWITCH_CHANNELS', '').split(',')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '30'))
        
        # Set up paths
        self.output_dir = '/output'
        
        # Dictionary to track active downloads
        self.active_downloads = {}
        self.twitch = None
        
        # Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate that all required configuration is present."""
        required_vars = {
            'TWITCH_CLIENT_ID': self.client_id,
            'TWITCH_CLIENT_SECRET': self.client_secret,
            'TWITCH_OAUTH_TOKEN': self.oauth_token,
            'TWITCH_CHANNELS': self.channels
        }
        
        missing_vars = [k for k, v in required_vars.items() if not v]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        if not self.oauth_token.startswith('oauth:'):
            raise ValueError("TWITCH_OAUTH_TOKEN must start with 'oauth:'")

    async def setup_twitch_client(self):
        """Initialize the Twitch API client with authentication."""
        self.twitch = await Twitch(self.client_id, self.client_secret)
        await self.twitch.authenticate_app([])
        self.twitch.auto_refresh_auth = False  # Disable auto refresh as we're using a static token
        logger.info("Successfully authenticated with Twitch API")

    async def check_stream_status(self):
        """Check if monitored channels are live and manage downloads accordingly."""
        for channel in self.channels:
            try:
                # Get user ID from username
                user = await first(self.twitch.get_users(logins=[channel]))
                if not user:
                    logger.warning(f"Could not find user: {channel}")
                    continue
                
                stream = await first(self.twitch.get_streams(user_id=user.id))
                
                if stream and channel not in self.active_downloads:
                    # Stream is live and not being recorded
                    logger.info(f"Starting download for {channel} - {stream.title}")
                    await self._start_download(channel, stream)
                    
                elif not stream and channel in self.active_downloads:
                    # Stream ended
                    logger.info(f"Stream ended for {channel} - stopping download")
                    self._stop_download(channel)
                    
            except Exception as e:
                logger.error(f"Error checking status for {channel}: {str(e)}")

    async def _start_download(self, channel, stream):
        """
        Start downloading a stream using streamlink with FFmpeg muxing.
        
        Args:
            channel (str): The channel name
            stream: Stream object from Twitch API
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss")
        filename = f"{timestamp} {channel} {stream.title.replace('/', '_')[:50]}.mp4"
        output_file = os.path.join(self.output_dir, filename)

        # Launch streamlink with the appropriate arguments.
        streamlink_command = [
            'streamlink',
            '--twitch-api-header', f'Authorization={self.oauth_token}',
            '--stream-segment-threads', '5',
            '--twitch-disable-ads',
            '--retry-max', '10',
            '--retry-streams', '30',
            '--output', output_file,
            f'https://twitch.tv/{channel}',
            'best',
        ]

        try:
            # Start streamlink process with specific pipe settings
            self.active_downloads[channel] = await asyncio.create_subprocess_exec(*streamlink_command)
            
        except Exception as e:
            logger.error(f"Failed to start download for {channel}: {str(e)}")
            self._stop_download(channel)


    def _stop_download(self, channel):
        """Stop and cleanup active downloads."""
        if channel in self.active_downloads:
            try:
                self.active_downloads[channel].terminate()
            except:
                pass
            del self.active_downloads[channel]

    async def run(self):
        """Main execution loop."""
        await self.setup_twitch_client()
        logger.info(f"Starting Twitch Archiver - monitoring channels: {', '.join(self.channels)}")
        
        while True:
            try:
                await self.check_stream_status()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                # Wait a bit before retrying after an error
                await asyncio.sleep(5)

if __name__ == "__main__":
    archiver = TwitchArchiver()
    asyncio.run(archiver.run())