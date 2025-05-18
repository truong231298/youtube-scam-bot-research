import json
from googleapiclient.discovery import build

class YouTubeClient:
    def __init__(self, api_key_path='config.json'):
        with open(api_key_path, 'r') as f:
            config = json.load(f)
        self.api_key = config['api_key']
        self.client = build("youtube", "v3", developerKey=self.api_key)

    def get_comments(self, video_id, max_results=100):
        comments = []
        request = self.client.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": top_comment["authorDisplayName"],
                "text": top_comment["textDisplay"],
                "published_at": top_comment["publishedAt"]
            })

        return comments
