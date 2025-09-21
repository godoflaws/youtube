import os
import requests
import random
import gdrive_utils
from constants import QUOTES_DIR, BCG_VIDEO_DIR, BCG_VIDEO_ID, PEXEL_KEYWORDS

# Constants
PEXEL_KEY = "y5p47lBGl0Xk2k8jMN4L2XfDbGzW1Yzxem1ZEnx0eDvK1eZ1FMzEJW14"
QUERY = random.sample(PEXEL_KEYWORDS, 10)
PER_PAGE = 1
PEXELS_URL = "https://api.pexels.com/videos/search"
HEADERS = {
    "Authorization": PEXEL_KEY
}

def fetch_and_save_videos():

    # Sort files for consistent page-to-set mapping
    json_files = sorted([f for f in os.listdir(QUOTES_DIR) if f.endswith(".json")])

    # Start with page 1
    for idx, filename in enumerate(json_files, start=1):
        set_name = filename.replace(".json", "")
        print(f"\n🔍 Fetching video for {set_name} (page {idx})...")

        # Use page number to vary the result
        params = {
            "query": QUERY[idx-1],
            "per_page": PER_PAGE,
            "page": random.choice([1,2,3])
        }
        response = requests.get(PEXELS_URL, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            if data["videos"]:
                video = data["videos"][0]
                # Prefer highest resolution
                video_file = sorted(video["video_files"], key=lambda x: -x["height"])[0]
                video_url = video_file["link"]
                video_user = video["user"]["name"]

                print(f"🎥 Video by: {video_user}")
                print(f"⬇️  Downloading: {video_url}")

                video_response = requests.get(video_url)
                if video_response.status_code == 200:
                    output_file_name = f"{set_name}.mp4"
                    # Write the video content to a local file
                    with open(f"{BCG_VIDEO_DIR}/{set_name}.mp4", "wb") as f:
                        f.write(video_response.content)
                    # Upload the video bytes to Google Drive
                    file_id = gdrive_utils.upload_bytes_to_drive(
                        filename=output_file_name,
                        file_path=f"{BCG_VIDEO_DIR}/{set_name}.mp4",
                        folder_id=BCG_VIDEO_ID,
                        mimetype="video/mp4"  # specify correct MIME type for videos
                    )
                    print(f"✅ Uploaded {output_file_name} to Drive with file ID: {file_id}")
                else:
                    print(f"❌ Failed to download video: {video_response.status_code}")
            else:
                print("❌ No videos found on this page.")
        else:
            print(f"❌ API request failed: {response.status_code} - {response.text}")

# fetch_and_save_videos()