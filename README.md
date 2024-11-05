# twitch-archiver

This is a Docker container that auto-archives twitch streams.

It uses an OAuth token from twitch to avoid ads on subscribed channels.

I set this up to download streams to a folder served by Plex.

## Usage

1. Create a docker-compose.yaml

```yaml
services:
  twitch-archiver:
    image: avalonlee/twitch-archiver:latest
    environment:
      # Get from Twitch Developer Console: https://dev.twitch.tv/console/apps
      # Hint: use "https://localhost" as the redirect URL for your app.
      - TWITCH_CLIENT_ID=your_client_id
      - TWITCH_CLIENT_SECRET=your_client_secret
      # Get OAuth token from: https://twitchapps.com/tmi/
      - TWITCH_OAUTH_TOKEN=oauth:your_token_here
      # Comma-separated list of channels to monitor
      - TWITCH_CHANNELS=channel1,channel2,channel3
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

## Example Output

```console
avalon@homelab:~/docker/downloaders$ docker compose logs twitch-archiver 
twitch-archiver-1  | 2024-11-04 01:00:16,432 - INFO - Successfully authenticated with Twitch API
twitch-archiver-1  | 2024-11-04 01:00:16,433 - INFO - Starting Twitch Archiver - monitoring channels: paymoneywubby
twitch-archiver-1  | 2024-11-04 15:21:44,268 - INFO - Starting download for paymoneywubby - Live with Drip
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
twitch-archiver-1  | 2024-11-04 17:38:16,866 - INFO - Stream ended for paymoneywubby - stopping download
twitch-archiver-1  | [cli][info] Stream ended
twitch-archiver-1  | Interrupted! Exiting...
twitch-archiver-1  | [cli][info] Closing currently open stream...

avalon@homelab:~/docker/downloaders$ ls /mnt/hdd1/media/streams/ -lh
-rwxrwxrwx 1 root root 5.9G Nov  5 01:38 '2024-11-04 15h21m44s paymoneywubby Live with Drip.mp4'
```

The stream shows up on Plex for immediate playback while the stream downloads.

![image](https://github.com/user-attachments/assets/2b32144e-f01c-45f3-96e3-3cc01fc88732)
