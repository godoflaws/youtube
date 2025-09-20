import os
import json
import gdrive_utils
from io import BytesIO
from gdrive_utils import upload_bytes_to_drive 
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    AudioFileClip,
    ColorClip
)
from moviepy.video.tools.segmenting import findObjects
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
from constants import BASE_TIME, READING_SPEED, PAUSE_TIME, QUOTES_DIR, QUOTES_ID, AUDIO_DIR, BCG_VIDEO_DIR, BCG_VIDEO_ID, VIDEO_DIR, VIDEO_ID
from moviepy.video.fx.all import fadein, fadeout
from PIL import Image
import asyncio
import tempfile
import edge_tts
import json, random

# Pillow patch (for compatibility with Pillow>=10)
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

os.makedirs(VIDEO_DIR, exist_ok=True)

# One-time function definition
async def synthesize_to_tempfile(text, voice="en-US-AriaNeural"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(tmp.name)
    return tmp.name

def calc_duration(quote_text):
    """Calculate duration based on text length + base + pause."""
    read_time = len(quote_text) / READING_SPEED
    return BASE_TIME + read_time + PAUSE_TIME


def typewriter_static_layout_clip(full_text, total_duration,
                                  font="Georgia", fontsize=70,
                                  color="white", max_width=1000,
                                  box_color=(0, 0, 0), box_opacity=0.6,
                                  video_size=(1080, 1920)):

    import textwrap

    # Parameters
    margin = 40
    line_spacing = 20
    word_spacing = 20

    # Break full text into words
    words = full_text.strip().split()

    # 1. Measure each word
    rendered_words = []
    for word in words:
        clip = TextClip(word, fontsize=fontsize, font=font, color=color)
        rendered_words.append((word, clip.w, clip.h, clip))

    # 2. Word wrapping manually
    lines = []
    current_line = []
    current_width = 0

    for word, w, h, clip in rendered_words:
        if current_line and current_width + w + word_spacing > max_width:
            lines.append(current_line)
            current_line = []
            current_width = 0
        current_line.append((word, w, h, clip))
        current_width += w + word_spacing

    if current_line:
        lines.append(current_line)

    # 3. Compute total text block size
    line_heights = [max(h for _, _, h, _ in line) for line in lines]
    total_height = sum(line_heights) + (len(lines) - 1) * line_spacing
    total_width = max(sum(w for _, w, _, _ in line) + (len(line) - 1) * word_spacing for line in lines)

    # 4. Starting top-left position (to center the text block)
    start_x = (video_size[0] - total_width) // 2
    start_y = (video_size[1] - total_height) // 2

    # 5. Place each word at its final destination
    word_clips = []
    typing_duration = total_duration * 0.7
    hold_duration = total_duration * 0.3
    word_index = 0
    word_count = len(rendered_words)
    word_duration = typing_duration / word_count

    y = start_y
    for line_idx, line in enumerate(lines):
        line_height = line_heights[line_idx]
        line_width = sum(w for _, w, _, _ in line) + (len(line) - 1) * word_spacing
        x = (video_size[0] - line_width) // 2

        for word, w, h, clip in line:
            appear_time = word_index * word_duration
            fade_duration = min(0.3, word_duration * 0.8)  # Ensure fade duration is shorter than word appearance
            word_clip = (
                clip.set_position((x, y))
                    .set_start(appear_time)
                    .set_duration(total_duration - appear_time)
                    .fadein(fade_duration)
            )
            word_clips.append(word_clip)
            x += w + word_spacing
            word_index += 1

        y += line_height + line_spacing

    # 6. Background box
    box = ColorClip(size=(total_width + margin, total_height + margin), color=box_color)
    box = box.set_opacity(box_opacity).set_duration(total_duration).set_position("center")

    # 7. Combine everything
    return CompositeVideoClip([box] + word_clips, size=video_size).set_duration(total_duration)


def create_video_for_set(set_name, quotes_path, audio_path, video_path, output_path):
    # Load quotes
    with open(quotes_path, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    # Load voice
    with open("voices.json", "r", encoding="utf-8") as f:
        voices = json.load(f)
    random_voice = random.choice(voices)    

    pause = AudioSegment.silent(duration=PAUSE_TIME*1000)
    final_audio = AudioSegment.empty()

    # Load background video
    base_video = VideoFileClip(video_path).resize(height=1920)
    base_video = base_video.crop(width=1080, x_center=base_video.w / 2)

    # Build text clips with durations
    text_clips = []
    for item in quotes:
        
        quote = item['quote']
        author = item['author']
        combined_text = f"“{quote}”\n\n— {author}"

        # Run the async function inside sync code
        mp3_path = asyncio.run(synthesize_to_tempfile(quote, random_voice))

        # Load into pydub and append
        audio = AudioSegment.from_file(mp3_path, format="mp3")
        final_audio += audio + pause

        txt_with_box = typewriter_static_layout_clip(combined_text, (audio + pause).duration_seconds)
        text_clips.append(txt_with_box)

    # Export final audio file
    final_audio.export(audio_path, format="mp3")
    # Load narration audio
    narration = AudioFileClip(audio_path)
    # Total duration from text timings
    total_duration = narration.duration

    # Sequence of quotes
    quotes_sequence = concatenate_videoclips(text_clips, method="compose")

    # Loop background video to match
    bg_video = base_video.loop(duration=total_duration).subclip(0, total_duration)

    # Composite video + audio
    final = CompositeVideoClip([bg_video, quotes_sequence]).set_audio(narration).set_duration(total_duration)

    # Export
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")
    
    file_id = gdrive_utils.upload_file(
        f"{set_name}.mp4",
        VIDEO_ID,
        output_path,
        mimetype="video/mp4"
    )

def create_final_video():
    # Download all JSON files from the Drive folder
    files = gdrive_utils.list_files(QUOTES_ID)
    for f in files:
        if f["name"].endswith(".json"):
            set_name = f["name"].rsplit(".", 1)[0]  # remove the .json extension
            quotes_file_id = f["id"]
            gdrive_utils.download_file(quotes_file_id, f"{QUOTES_DIR}/{set_name}.json")

    # Download all bcg mp4 files from the Drive folder
    files = gdrive_utils.list_files(BCG_VIDEO_ID)
    for f in files:
        if f["name"].endswith(".mp4"):
            set_name = f["name"].rsplit(".", 1)[0]  # remove the .mp4 extension
            bcg_video_file_id = f["id"]
            gdrive_utils.download_file(bcg_video_file_id, f"{BCG_VIDEO_DIR}/{set_name}.mp4")

    for set_file in os.listdir(QUOTES_DIR):
        if set_file.endswith(".json"):
            set_name = os.path.splitext(set_file)[0]
            quotes_path = os.path.join(QUOTES_DIR, set_file)
            audio_path = os.path.join(AUDIO_DIR, f"{set_name}.mp3")
            video_path = os.path.join(BCG_VIDEO_DIR, f"{set_name}.mp4")
            output_path = os.path.join(VIDEO_DIR, f"{set_name}.mp4")

            if not os.path.exists(audio_path):
                print(f"⚠️ Skipping {set_name}: No audio file found at {audio_path}")
                continue

            print(f"🎬 Creating video for {set_file}...")
            create_video_for_set(set_name, quotes_path, audio_path, video_path, output_path)

    print("✅ All videos created with narration!")

# create_final_video()