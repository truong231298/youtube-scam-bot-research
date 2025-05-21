# src/fetch_video_list.py
import os
import pandas as pd
from youtube_client import YouTubeClient

def main():
    # Khởi tạo client
    client = YouTubeClient()

    # Đọc danh sách channel
    channels_csv = os.path.join('data', 'channels.csv')
    df_chan = pd.read_csv(channels_csv)
    channel_ids = df_chan['channel_id'].tolist()

    records = []
    for cid in channel_ids:
        try:
            # Lấy tối đa 50 video mới nhất
            vids = client.search_videos_by_channel(cid, max_results=50)
            metas = client.fetch_video_metadata(vids)
            for m in metas:
                # Thêm trường channel_id để dễ theo dõi
                m['channel_id'] = cid
            records.extend(metas)
            print(f"Processed channel {cid}: {len(vids)} videos")
        except Exception as e:
            print(f"Error with channel {cid}: {e}")

    # Lưu kết quả
    os.makedirs('data', exist_ok=True)
    df_videos = pd.DataFrame(records)
    df_videos.to_csv(os.path.join('data', 'video_list.csv'), index=False)
    print(f"Saved {len(df_videos)} records to data/video_list.csv")

if __name__ == "__main__":
    main()
