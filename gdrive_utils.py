import os
from io import BytesIO
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def upload_bytes_to_drive(filename, file_bytes, folder_id, service):
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/octet-stream")
    file_metadata = {"name": filename, "parents": [folder_id]}
    
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    
    print(f"✅ Uploaded {filename} to Drive (file id: {uploaded.get('id')})")
    return uploaded.get("id")


def get_drive_service():
    creds = Credentials(
        None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds)

drive_service = get_drive_service()


def upload_file(file_name: str, file_bytes: bytes, folder_id: str) -> str:
    """Upload a file to Google Drive from bytes. Returns file ID."""
    file_metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaIoBaseUpload(BytesIO(file_bytes), mimetype="video/mp4")
    uploaded_file = drive_service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()
    return uploaded_file["id"]


def list_files(folder_id: str):
    """List all files in a folder."""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])


def download_file(file_id: str, output_path: str):
    """Download a file from Drive to local path."""
    request = drive_service.files().get_media(fileId=file_id)
    with open(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()


def delete_file(file_id: str):
    """Delete a file from Google Drive."""
    drive_service.files().delete(fileId=file_id).execute()

def delete_file_by_name(filename: str, folder_id: str):
    query = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    results = drive_service.files().list(
        q=query, fields="files(id, name)"
    ).execute()

    files = results.get("files", [])
    if not files:
        print(f"⚠️ No file named {filename} found.")
        return
    
    # Delete all matching files (in case there are multiple with same name)
    for f in files:
        try:
            delete_file(f["id"])
            print(f"🗑️ Deleted {f['name']} (ID={f['id']})")
        except Exception as e:
            print(f"❌ Could not delete {f['name']}: {e}")
