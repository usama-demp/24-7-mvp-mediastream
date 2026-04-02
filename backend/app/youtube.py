# # app/youtube.py
# import requests

# YOUTUBE_API_KEY = "AIzaSyCM8S6nV3kRmXkOTOQiNK4gsQdg4wuJxS4"  # replace with your API key
# YOUTUBE_API_SEARCH = "https://www.googleapis.com/youtube/v3/search"
# YOUTUBE_API_CHANNELS = "https://www.googleapis.com/youtube/v3/channels"

# def get_channel_id_by_name(channel_name: str):
#     """
#     Search YouTube for the channel name and return the channelId
#     """
#     params = {
#         "part": "snippet",
#         "q": channel_name,
#         "type": "channel",
#         "key": YOUTUBE_API_KEY,
#         "maxResults": 1
#     }
#     response = requests.get(YOUTUBE_API_SEARCH, params=params)
#     data = response.json()
#     items = data.get("items")
#     if not items:
#         return None
#     return items[0]["snippet"]["channelId"]

# def get_live_video_url(channel_id: str):
#     """
#     Check if the channel has a live video and return the embed URL
#     """
#     params = {
#         "part": "snippet",
#         "channelId": channel_id,
#         "eventType": "live",
#         "type": "video",
#         "key": YOUTUBE_API_KEY,
#         "maxResults": 1
#     }
#     response = requests.get(YOUTUBE_API_SEARCH, params=params)
#     data = response.json()
#     items = data.get("items")
#     if not items:
#         return None
#     video_id = items[0]["id"]["videoId"]
#     return f"https://www.youtube.com/embed/{video_id}?autoplay=1"

# app/youtube.py
import requests

YOUTUBE_API_KEY = "AIzaSyCWK36zn_VvSvcHBjaliEqfkmiXFP418y4"  # Replace with your YouTube Data API key
YOUTUBE_CHANNEL_API = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_SEARCH_API = "https://www.googleapis.com/youtube/v3/search"

def get_channel_id_by_name(channel_name: str) -> str | None:
    """
    Get YouTube channel ID by channel name.
    """
    try:
        params = {
            "part": "id",
            "forUsername": channel_name,
            "key": YOUTUBE_API_KEY
        }
        response = requests.get(YOUTUBE_CHANNEL_API, params=params)
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["id"]
        # If not found by username, try search by name
        params = {
            "part": "snippet",
            "q": channel_name,
            "type": "channel",
            "key": YOUTUBE_API_KEY,
            "maxResults": 1
        }
        response = requests.get(YOUTUBE_SEARCH_API, params=params)
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["snippet"]["channelId"]
    except Exception as e:
        print(f"[get_channel_id_by_name] Error: {e}")
    return None

def get_live_video_url(channel_id: str) -> str | None:
    """
    Get current live video URL for a channel. Returns None if offline.
    """
    try:
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "eventType": "live",
            "type": "video",
            "key": YOUTUBE_API_KEY,
            "maxResults": 1
        }
        response = requests.get(YOUTUBE_SEARCH_API, params=params)
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        print(f"[get_live_video_url] Error: {e}")
    return None