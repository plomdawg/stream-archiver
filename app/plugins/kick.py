"""
Streamlink plugin for Kick.com
Based on the community plugin from https://github.com/nonvegan/streamlink-plugin-kick
"""

import re
from streamlink.plugin import Plugin, pluginmatcher, PluginError
from streamlink.stream import HLSStream

import cloudscraper


@pluginmatcher(re.compile(r"https?://(?:www\.)?kick\.com/(?P<channel>[^/?&]+)"))
class KickPlugin(Plugin):
    _API_URL = "https://kick.com/api/v2/channels/{channel}/livestream"
    _VOD_URL = "https://kick.com/api/v1/video/{video_id}"
    _CLIP_URL = "https://kick.com/api/v2/clips/{clip_id}"

    def __init__(self, a, url, options=None):
        super().__init__(a, url, options or {})
        self.cloudscraper = cloudscraper.create_scraper()

    def _get_streams(self):
        channel = self.match.group("channel")

        # Check if it's a VOD or clip URL
        vod_match = re.search(r"/video/([^/?&]+)", self.url)
        clip_match = re.search(r"clip=([^/?&]+)", self.url)

        if vod_match:
            return self._get_vod_streams(vod_match.group(1))
        elif clip_match:
            return self._get_clip_streams(clip_match.group(1))
        else:
            return self._get_live_streams(channel)

    def _get_live_streams(self, channel):
        """Get live stream data"""
        try:
            response = self.cloudscraper.get(self._API_URL.format(channel=channel))
            response.raise_for_status()
            data = response.json()

            if not data or not data.get("data"):
                self.logger.error(f"No stream data found for channel: {channel}")
                return {}

            stream_data = data["data"]
            playback_url = stream_data.get("playback_url")

            if not playback_url:
                self.logger.error(f"No playback URL found for channel: {channel}")
                return {}

            return HLSStream.parse_variant_playlist(self.session, playback_url)

        except Exception as e:
            self.logger.error(f"Error fetching live stream for {channel}: {str(e)}")
            raise PluginError(f"Failed to get live stream data: {str(e)}")

    def _get_vod_streams(self, video_id):
        """Get VOD stream data"""
        try:
            response = self.cloudscraper.get(self._VOD_URL.format(video_id=video_id))
            response.raise_for_status()
            data = response.json()

            if not data or not data.get("data"):
                self.logger.error(f"No VOD data found for video: {video_id}")
                return {}

            vod_data = data["data"]
            playback_url = vod_data.get("source")

            if not playback_url:
                self.logger.error(f"No playback URL found for VOD: {video_id}")
                return {}

            return HLSStream.parse_variant_playlist(self.session, playback_url)

        except Exception as e:
            self.logger.error(f"Error fetching VOD for {video_id}: {str(e)}")
            raise PluginError(f"Failed to get VOD data: {str(e)}")

    def _get_clip_streams(self, clip_id):
        """Get clip stream data"""
        try:
            response = self.cloudscraper.get(self._CLIP_URL.format(clip_id=clip_id))
            response.raise_for_status()
            data = response.json()

            if not data or not data.get("clip"):
                self.logger.error(f"No clip data found for clip: {clip_id}")
                return {}

            clip_data = data["clip"]
            playback_url = clip_data.get("video_url")

            if not playback_url:
                self.logger.error(f"No playback URL found for clip: {clip_id}")
                return {}

            return HLSStream.parse_variant_playlist(self.session, playback_url)

        except Exception as e:
            self.logger.error(f"Error fetching clip for {clip_id}: {str(e)}")
            raise PluginError(f"Failed to get clip data: {str(e)}")


def get_kick_stream_info(channel: str) -> dict:
    """
    Helper function to get Kick stream information for a channel.
    Returns dict with 'is_live', 'title', etc. or empty dict if error.
    """
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(f"https://kick.com/api/v2/channels/{channel}/livestream")
        response.raise_for_status()
        data = response.json()

        if not data or not data.get("data"):
            return {}

        stream_data = data["data"]
        playback_url = stream_data.get("playback_url")

        # Extract stream info
        result = {
            "is_live": bool(playback_url),
            "channel": channel,
        }

        if playback_url:
            # Stream is live, get additional metadata
            result["session_title"] = stream_data.get(
                "session_title", f"Kick Stream - {channel}"
            )
            result["playback_url"] = playback_url

        return result

    except Exception as e:
        # Return empty dict on any error
        return {}


__plugin__ = KickPlugin
