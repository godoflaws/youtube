import os
import random
import time
from final_video import create_final_video
from pexels_video import fetch_and_save_videos
from zenquotes import fetch_and_save_quotes
from constants import QUOTES_DIR, AUDIO_DIR, BCG_VIDEO_DIR, VIDEO_DIR, youtube_descriptions, youtube_tags, youtube_titles
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
     # Construct associated file paths
     related_files = [
        os.path.join(VIDEO_DIR, base_name + ".mp4"),   # Final video
        os.path.join(BCG_VIDEO_DIR, base_name + ".mp4"),   # Background video
        os.path.join(AUDIO_DIR, base_name + ".mp3"), # Audio file
        os.path.join(QUOTES_DIR, base_name + ".json"), # Quote file
     ]

     # Delete each associated file if it exists
     for path in related_files:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted: {path}")
        else:
            print(f"Not found: {path}")

def workflow():
    os.makedirs(VIDEO_DIR, exist_ok=True)
    mp4_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]

    if not mp4_files:
        create_mp4_files()
    else:
        file_to_process = mp4_files[0]
        process_mp4(file_to_process)
        cleanup_files(os.path.splitext(file_to_process)[0])

# workflow()
