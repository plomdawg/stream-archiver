# stream-archiver

This is a Docker container that auto-archives live streams from **Twitch** and **Kick**.

For Twitch streams, it uses an OAuth token to avoid ads on subscribed channels.
For Kick streams, it uses streamlink with a custom plugin to monitor and download streams.

I set this up to download streams to a folder served by Plex.

## Usage

1. Create a docker-compose.yaml

```yaml
services:
  stream-archiver:
    image: avalonlee/stream-archiver:latest
    environment:
      # === TWITCH CONFIGURATION  ===
      # Get from Twitch Developer Console: https://dev.twitch.tv/console/apps
      # Hint: use "https://localhost" as the redirect URL for your app.
      - TWITCH_CLIENT_ID=your_client_id
      - TWITCH_CLIENT_SECRET=your_client_secret
      # Get OAuth token from: https://twitchapps.com/tmi/
      - TWITCH_OAUTH_TOKEN=oauth:your_token_here
      # Comma-separated list of Twitch channels to monitor
      - TWITCH_CHANNELS=paymoneywubby
      
      # === KICK CONFIGURATION ===
      # Comma-separated list of Kick channels to monitor
      - KICK_CHANNELS=paymoneywubby
      
      # === GENERAL SETTINGS ===
      # How often to check if streams are live (in seconds)
      - CHECK_INTERVAL=30
      # Your timezone, e.g., America/New_York, Europe/London, etc.
      - TZ=America/Los_Angeles
    volumes:
      # Where to store the downloaded videos
      - ./output:/output
    restart: unless-stopped
```

1. Run the container

```bash
docker compose up -d
```

## Platform Support

### Twitch 🎮
- **Requirements**: Client ID, Client Secret, and OAuth Token
- **Features**: Ad-free recording for subscribed channels
- **Setup**: Get credentials from [Twitch Developer Console](https://dev.twitch.tv/console/apps) and OAuth token from [twitchapps.com](https://twitchapps.com/tmi/)

### Kick ⚡
- **Requirements**: Just channel names (no authentication needed)  
- **Features**: Direct stream recording using custom streamlink plugin
- **Setup**: Simply add channel names to `KICK_CHANNELS`

You can configure **both platforms simultaneously** or use just one - the archiver will automatically detect which platforms are configured and monitor accordingly.

## Example Output

```console
avalon@homelab:~/docker/downloaders$ docker compose logs stream-archiver 
stream-archiver-1  | 2024-11-04 01:00:16,432 - INFO - 🎮 Successfully authenticated with Twitch API
stream-archiver-1  | 2024-11-04 01:00:16,433 - INFO - ⚡ Successfully initialized Kick platform
stream-archiver-1  | 2024-11-04 01:00:16,434 - INFO - 🚀 Starting Stream Archiver - monitoring Twitch: paymoneywubby | Kick: paymoneywubby
stream-archiver-1  | 2024-11-04 15:21:44,268 - INFO - 🔴 Starting download for Twitch channel paymoneywubby - Live with Drip
twitch-archiver-1  | [cli][info] streamlink is running as root! Be careful!
twitch-archiver-1  | [cli][info] Found matching plugin twitch for URL https://twitch.tv/paymoneywubby
twitch-archiver-1  | [cli][info] Available streams: audio_only, 160p (worst), 360p, 480p, 720p, 1080p (best)
twitch-archiver-1  | [cli][info] Opening stream: 1080p (hls)
twitch-archiver-1  | [cli][info] Writing output to
twitch-archiver-1  | /output/2024-11-04 15h21m44s paymoneywubby Live with Drip.mp4
twitch-archiver-1  | [plugins.twitch][info] Will skip ad segments
twitch-archiver-1  | [plugins.twitch][info] Waiting for pre-roll ads to finish, be patient
twitch-archiver-1  | [stream.hls][info] Filtering out segments and pausing stream output
twitch-archiver-1  | [stream.hls][warning] Encountered a stream discontinuity. This is unsupported and will result in incoherent output data.
twitch-archiver-1  | [stream.hls][info] Resuming stream output
stream-archiver-1  | 2024-11-04 17:38:16,866 - INFO - ⏹️ Stream ended for Twitch channel paymoneywubby - stopping download
twitch-archiver-1  | [cli][info] Stream ended
twitch-archiver-1  | Interrupted! Exiting...
twitch-archiver-1  | [cli][info] Closing currently open stream...

avalon@homelab:~/docker/downloaders$ ls /mnt/hdd1/media/streams/ -lh
-rwxrwxrwx 1 root root 5.9G Nov  5 01:38 '2024-11-04 15h21m44s ttv paymoneywubby Live with Drip.mp4'
-rwxrwxrwx 1 root root 3.2G Nov  5 02:15 '2024-11-04 16h15m22s kick paymoneywubby Gambling Stream.mp4'
```

The stream shows up on Plex for immediate playback while the stream downloads.

![image](https://github.com/user-attachments/assets/2b32144e-f01c-45f3-96e3-3cc01fc88732)
