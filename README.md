# stream-archiver

This is a Docker container that auto-archives live streams from **Twitch** and **Kick**.

For Twitch streams, it uses an OAuth token to avoid ads on subscribed channels.
For Kick streams, it uses streamlink with a custom plugin to monitor and download streams.

I set this up to download streams to a folder served by Plex.

## Usage

### Quick Start

Twitch only:

```bash
docker run -d \
  -v ./output:/output \
  -e TWITCH_CLIENT_ID=your_client_id \
  -e TWITCH_CLIENT_SECRET=your_client_secret \
  -e TWITCH_OAUTH_TOKEN=oauth:your_token_here \
  -e TWITCH_CHANNELS=paymoneywubby \
  avalonlee/stream-archiver:latest
```

Kick only:

```bash
docker run -d \
  -v ./output:/output \
  -e KICK_CHANNELS=paymoneywubby \
  avalonlee/stream-archiver:latest
```

Both:

```bash
docker run -d \
  -v ./output:/output \
  -e TWITCH_CLIENT_ID=your_client_id \
  -e TWITCH_CLIENT_SECRET=your_client_secret \
  -e TWITCH_OAUTH_TOKEN=oauth:your_token_here \
  -e TWITCH_CHANNELS=paymoneywubby \
  -e KICK_CHANNELS=paymoneywubby \
  avalonlee/stream-archiver:latest
```

### Using Docker Compose

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
stream-archiver-1  | 2025-08-05 23:00:29,935 - INFO - 🎮 Successfully authenticated with Twitch API
stream-archiver-1  | 2025-08-05 23:00:29,935 - INFO - ⚡ Successfully initialized Kick platform
stream-archiver-1  | 2025-08-05 23:00:29,935 - INFO - 🚀 Starting Stream Archiver - monitoring Twitch: paymoneywubby | Kick: paymoneywubby
stream-archiver-1  | 2025-08-05 23:00:31,050 - INFO - 🔴 Starting download for Kick channel paymoneywubby - Live with Drip
stream-archiver-1  | [cli][info] streamlink is running as root! Be careful!
stream-archiver-1  | [cli][info] Found matching plugin kick for URL https://kick.com/paymoneywubby
stream-archiver-1  | [cli][info] Available streams: 160p (worst), 360p, 480p, 720p, 1080p (best)
stream-archiver-1  | [cli][info] Opening stream: 1080p (hls)
stream-archiver-1  | [cli][info] Writing output to
stream-archiver-1  | /output/2025-08-05 23:00 kick paymoneywubby Live with Drip.mp4
stream-archiver-1  | [cli][info] Stream ended
stream-archiver-1  | [cli][info] Closing currently open stream...
stream-archiver-1  | 2025-08-06 08:08:44,480 - INFO - ⏹️ Stream ended for Kick channel paymoneywubby - stopping download

avalon@homelab:~/docker/downloaders$ ls /nas/streams/ -lh
-rwxrwxrwx 1 root root 2.9G Aug  5 01:38 '2025-08-05 23:00 kick paymoneywubby Live with Drip.mp4'
-rwxrwxrwx 1 root root 1.5G Aug  4 02:15 '2025-08-04 15:21 ttv paymoneywubby MEDIA SHARE.mp4'
```

The stream shows up on my Plex server for immediate playback while the stream downloads.

![image](https://github.com/user-attachments/assets/2b32144e-f01c-45f3-96e3-3cc01fc88732)
