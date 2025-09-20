import os
import random
import time
from gdrive_utils import delete_file_by_name
from final_video import create_final_video
from pexels_video import fetch_and_save_videos
from zenquotes import fetch_and_save_quotes
from constants import QUOTES_ID, AUDIO_ID, BCG_VIDEO_ID, VIDEO_DIR, VIDEO_ID, youtube_descriptions, youtube_tags, youtube_titles
from youtube_upload import upload_video

def create_mp4_files():
    fetch_and_save_quotes()
    fetch_and_save_videos()
    create_final_video()

def process_mp4(file_path):
    random_title = random.choice(youtube_titles)
    random_tags = random.choice(youtube_tags)
    random_description = random.choice(youtube_descriptions)
    video_id = upload_video(
        file_path,
        title=random_title,
        description=random_description,
        tags=random_tags,
        privacy_status="public",
    )

def cleanup_files(base_name):
     delete_file_by_name(base_name + ".mp4", VIDEO_ID)
     delete_file_by_name(base_name + ".mp4", BCG_VIDEO_ID)
     delete_file_by_name(base_name + ".json", QUOTES_ID)

def workflow():
    # Download all mp4 files from the Drive folder
    files = gdrive_utils.list_files(VIDEO_ID)
    for f in files:
        if f["name"].endswith(".mp4"):
            set_name = f["name"].rsplit(".", 1)[0]  # remove the .mp4 extension
            video_file_id = f["id"]
            gdrive_utils.download_file(video_file_id, f"{VIDEO_DIR}/{set_name}.mp4")
    mp4_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]

    if not mp4_files:
        create_mp4_files()
    else:
        file_to_process = mp4_files[0]
        process_mp4(file_to_process)
        cleanup_files(os.path.splitext(file_to_process)[0])

# workflow()
