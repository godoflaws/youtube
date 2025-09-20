import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# Path to your service account JSON key file
SERVICE_ACCOUNT_FILE = "service_account.json"

# Scopes required to read/write files in Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Initialize Drive service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)


def upload_bytes_to_drive(filename: str, file_bytes: bytes, folder_id: str, mimetype="application/octet-stream") -> str:
    """Upload a file to Google Drive from bytes."""
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mimetype)
    file_metadata = {"name": filename, "parents": [folder_id]}
    
    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    
    print(f"✅ Uploaded {filename} to Drive (file id: {uploaded.get('id')})")
    return uploaded.get("id")


def upload_file_from_path(file_path: str, folder_id: str, mimetype="application/octet-stream") -> str:
    """Upload a local file to Google Drive."""
    filename = file_path.split("/")[-1]
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return upload_bytes_to_drive(filename, file_bytes, folder_id, mimetype)


def list_files(folder_id: str):
    """List all files in a folder."""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
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
    """Delete all files with a given name inside a specific folder."""
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
            print(f"❌ Could not delete {f['name']} from folder {folder_id}: {e}")
