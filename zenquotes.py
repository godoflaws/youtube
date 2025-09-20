import requests
import json
import os
import gdrive_utils
from constants import QUOTES_ID

api_url = "https://zenquotes.io/api/quotes/"

def fetch_and_save_quotes():
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return

    quotes = response.json()

    # break into sets of 5
    sets = [quotes[i:i+5] for i in range(0, len(quotes), 5)]

    for idx, quote_set in enumerate(sets, start=1):
        # prepare data as list of dicts
        formatted_set = [
            {"quote": q["q"], "author": q["a"]}
            for q in quote_set
        ]

        # Save each set into its own JSON file in Google Drive
        filename = f"set_{idx}.json"
        json_bytes = json.dumps(formatted_set, indent=4).encode("utf-8")  # convert JSON to bytes

        file_id = gdrive_utils.upload_bytes_to_drive(
            filename,        # e.g., "set_1.json"
            json_bytes,      # the actual bytes content
            QUOTES_ID,       # folder ID
            mimetype="application/json"
        )
        print(f"✅ Saved {filename} to Google Drive with File ID: {file_id}")

# fetch_and_save_quotes()
