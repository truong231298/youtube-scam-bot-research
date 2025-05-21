import sys
import json
from youtube_client import YouTubeClient
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_comments.py VIDEO_ID")
        sys.exit(1)

    video_id = sys.argv[1]
    client = YouTubeClient()
    comments = client.fetch_comment_threads(video_id)

    Path("data").mkdir(exist_ok=True)
    with open("data/sample_comments.json", "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2, ensure_ascii=False)

    print(f"Đã lưu {len(comments)} bình luận vào data/sample_comments.json")
