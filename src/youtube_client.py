import json
import os
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Thiết lập logging cơ bản
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeClient:
    """
    Wrapper tái sử dụng cho YouTube Data API v3.
    Đọc API key từ biến môi trường YOUTUBE_API_KEY hoặc file config.json.
    """

    def __init__(self, api_key: str = None, config_path: str = "config.json"):
        """
        Khởi tạo YouTubeClient.

        Thứ tự ưu tiên lấy API key:
        1. Tham số `api_key` truyền trực tiếp.
        2. Biến môi trường `YOUTUBE_API_KEY`.
        3. File `config.json` tại `config_path`.

        Raises:
            ValueError: nếu không tìm thấy API key.
        """
        if api_key:
            self.api_key = api_key
            logger.info("Sử dụng API key từ tham số.")
        else:
            self.api_key = os.getenv("YOUTUBE_API_KEY")
            if self.api_key:
                logger.info("Sử dụng API key từ biến môi trường.")
            elif os.path.exists(config_path):
                conf = json.load(open(config_path, "r", encoding="utf-8"))
                self.api_key = conf.get("api_key")
                if self.api_key:
                    logger.info(f"Sử dụng API key từ file {config_path}.")

        if not self.api_key:
            logger.error("Chưa cung cấp API key.")
            raise ValueError("Chưa cung cấp API key. Thiết lập biến YOUTUBE_API_KEY hoặc config.json.")

        # Khởi tạo client
        try:
            self.youtube = build("youtube", "v3", developerKey=self.api_key)
            logger.info("YouTube Data API client khởi tạo thành công.")
        except Exception as e:
            logger.exception("Lỗi khi khởi tạo YouTube client: %s", e)
            raise

    def fetch_video_metadata(self, video_ids: list[str]) -> list[dict]:
        """
        Lấy metadata cơ bản cho danh sách video IDs.

        Args:
            video_ids (list[str]): Danh sách YouTube video IDs.

        Returns:
            list[dict]: Mỗi dict chứa `video_id`, `title`, `published_at`, `view_count`.

        Raises:
            RuntimeError: nếu lỗi trong quá trình gọi API.
        """
        try:
            resp = (
                self.youtube.videos()
                .list(part="snippet,statistics", id=','.join(video_ids))
                .execute()
            )
            logger.info(f"Lấy metadata cho {len(video_ids)} video.")
        except HttpError as e:
            logger.error("Error fetching video metadata: %s", e)
            raise RuntimeError(f"Error fetching video metadata: {e}")

        results = []
        for item in resp.get("items", []):
            results.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
                "view_count": int(item["statistics"].get("viewCount", 0))
            })
        return results

    def fetch_comment_threads(self, video_id: str, max_results: int = 100) -> list[dict]:
        """
        Lấy bình luận cấp top-level cho 1 video.

        Args:
            video_id (str): Video ID cần thu thập bình luận.
            max_results (int): Số lượng bình luận tối đa (1-100).

        Returns:
            list[dict]: Danh sách dict với các trường:
                - comment_id
                - video_id
                - author
                - text
                - published_at
                - like_count

        Raises:
            RuntimeError: nếu lỗi trong quá trình gọi API.
        """
        comments = []
        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                textFormat="plainText"
            )
            response = request.execute()
            logger.info(f"Lấy {len(response.get('items', []))} bình luận cho video {video_id}.")
        except HttpError as e:
            logger.error("Error fetching comments for video %s: %s", video_id, e)
            raise RuntimeError(f"Error fetching comments for video {video_id}: {e}")

        for item in response.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "video_id": video_id,
                "author": s.get("authorDisplayName"),
                "text": s.get("textDisplay"),
                "published_at": s.get("publishedAt"),
                "like_count": int(s.get("likeCount", 0))
            })
        return comments

    def search_videos_by_channel(self, channel_id: str, max_results: int = 50) -> list[str]:
        """
        Lấy danh sách videoId mới nhất của một channel.

        Args:
            channel_id (str): ID của channel.
            max_results (int): Số video lấy tối đa.

        Returns:
            list[str]: Danh sách video IDs.

        Raises:
            RuntimeError: nếu lỗi gọi API.
        """
        video_ids = []
        try:
            req = self.youtube.search().list(
                part="id",
                channelId=channel_id,
                maxResults=max_results,
                order="date",
                type="video"
            )
            res = req.execute()
            logger.info(f"Lấy {len(res.get('items', []))} video mới nhất từ channel {channel_id}.")
        except HttpError as e:
            logger.error("Error searching videos for channel %s: %s", channel_id, e)
            raise RuntimeError(f"Error searching videos for channel {channel_id}: {e}")

        for item in res.get("items", []):
            vid = item["id"].get("videoId")
            if vid:
                video_ids.append(vid)
        return video_ids


if __name__ == "__main__":
    # Ví dụ sử dụng nhanh
    client = YouTubeClient()
    vids = client.search_videos_by_channel("UC_x5XG1OV2P6uZZ5FSM9Ttw", max_results=5)
    logger.info(f"Video IDs: {vids}")

    metas = client.fetch_video_metadata(vids)
    logger.info(f"Metadata: {metas}")

    for vid in vids:
        comments = client.fetch_comment_threads(vid, max_results=10)
        logger.info(f"Đã thu thập {len(comments)} bình luận cho {vid}.")
