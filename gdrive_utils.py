import os
from io import BytesIO
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload, MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from environment variables
creds = Credentials(
    None,  # No access token needed; will be fetched automatically
    refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.getenv("YOUTUBE_CLIENT_ID"),
    client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=creds)


def upload_bytes_to_drive(filename: str, file_path: str, folder_id: str, mimetype="application/octet-stream", max_retries=5) -> str:
    """
    Uploads a file to Google Drive using resumable upload with retry logic.
    Works for both small and large files.
    """
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)

    request = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    )

    for attempt in range(max_retries):
        try:
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"⬆️ Uploading {filename}: {int(status.progress() * 100)}%")
            print(f"✅ Uploaded {filename} (file id: {response.get('id')})")
            return response.get("id")
        except Exception as e:
            print(f"⚠️ Upload failed (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(2 ** attempt)  # exponential backoff before retry

    raise RuntimeError(f"❌ Upload failed after {max_retries} attempts for {filename}")



def list_files(folder_id: str):
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])


def download_file(file_id: str, output_path: str):
    request = drive_service.files().get_media(fileId=file_id)
    with open(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()


def delete_file(file_id: str):
    drive_service.files().delete(fileId=file_id).execute()


def delete_file_by_name(filename: str, folder_id: str):
    query = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        print(f"⚠️ No file named {filename} found in folder {folder_id}")
        return
    
    for f in files:
        try:
            delete_file(f["id"])
            print(f"🗑️ Deleted {f['name']} (ID={f['id']}) from folder {folder_id}")
        except Exception as e:
            print(f"❌ Could not delete {f['name']}: {e}")
